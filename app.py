from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import numpy as np
import pandas as pd
from scipy import stats
import json
import os

app = Flask(__name__)
CORS(app)

class ChiSquareUniformityTest:
    def __init__(self, n_numbers=100, n_intervals=10, alpha=0.05, random_seed=42):
        self.n_numbers = n_numbers
        self.n_intervals = n_intervals
        self.alpha = alpha
        self.random_seed = random_seed
        self.df = n_intervals - 1
        self.critical_value = stats.chi2.ppf(1 - alpha, self.df)
        
    def generate_random_numbers(self):
        """Generate uniform random numbers between 0 and 1"""
        np.random.seed(self.random_seed)
        self.random_numbers = np.random.uniform(0, 1, self.n_numbers)
        return self.random_numbers.tolist()
    
    def calculate_frequencies(self):
        """Calculate observed and expected frequencies"""
        self.interval_edges = np.linspace(0, 1, self.n_intervals + 1)
        self.observed, _ = np.histogram(self.random_numbers, bins=self.interval_edges)
        self.expected = np.full(self.n_intervals, self.n_numbers / self.n_intervals)
        return self.observed.tolist(), self.expected.tolist()
    
    def perform_chi_square_test(self):
        """Perform the complete chi-square test"""
        # Generate numbers and calculate frequencies
        random_nums = self.generate_random_numbers()
        observed, expected = self.calculate_frequencies()
        
        # Calculate components and test statistic
        results = []
        chi_square_components = []
        chi_square_statistic = 0
        
        for i in range(self.n_intervals):
            O_i = observed[i]
            E_i = expected[i]
            O_minus_E = O_i - E_i
            O_minus_E_squared = (O_minus_E) ** 2
            chi_component = O_minus_E_squared / E_i
            chi_square_statistic += chi_component
            
            results.append({
                'interval': i + 1,
                'range': f"{(i/self.n_intervals):.1f}-{((i+1)/self.n_intervals):.1f}",
                'observed': O_i,
                'expected': round(E_i, 1),
                'O_minus_E': round(O_minus_E, 1),
                'O_minus_E_squared': round(O_minus_E_squared, 2),
                'chi_component': round(chi_component, 4)
            })
        
        # Calculate p-value and make decision
        p_value = 1 - stats.chi2.cdf(chi_square_statistic, self.df)
        
        decision = "REJECT" if chi_square_statistic > self.critical_value else "FAIL TO REJECT"
        conclusion = "Numbers are NOT uniformly distributed" if decision == "REJECT" else "Numbers appear to be uniformly distributed"
        
        return {
            'test_parameters': {
                'n_numbers': self.n_numbers,
                'n_intervals': self.n_intervals,
                'alpha': self.alpha,
                'random_seed': self.random_seed,
                'df': self.df
            },
            'sample_statistics': {
                'sample_mean': round(np.mean(self.random_numbers), 4),
                'sample_variance': round(np.var(self.random_numbers), 4),
                'first_10_numbers': [round(x, 3) for x in self.random_numbers[:10]]
            },
            'test_results': {
                'chi_square': round(chi_square_statistic, 4),
                'critical_value': round(self.critical_value, 4),
                'p_value': round(p_value, 4),
                'decision': decision,
                'conclusion': conclusion
            },
            'frequency_table': results,
            'chart_data': {
                'intervals': [f"{(i/self.n_intervals):.1f}-{((i+1)/self.n_intervals):.1f}" for i in range(self.n_intervals)],
                'observed': observed,
                'expected': expected,
                'components': [round(((o-e)**2/e), 4) for o,e in zip(observed, expected)]
            }
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chi-square-test', methods=['POST'])
def chi_square_test():
    try:
        data = request.get_json()
        
        # Get parameters from request
        n_numbers = data.get('n_numbers', 100)
        n_intervals = data.get('n_intervals', 10)
        alpha = data.get('alpha', 0.05)
        random_seed = data.get('random_seed', 42)
        
        # Validate inputs
        if n_numbers <= 0 or n_intervals <= 0:
            return jsonify({'error': 'Sample size and intervals must be positive'}), 400
        
        # Perform chi-square test
        test = ChiSquareUniformityTest(n_numbers, n_intervals, alpha, random_seed)
        results = test.perform_chi_square_test()
        
        return jsonify({
            'success': True,
            'data': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/multiple-alpha-test', methods=['POST'])
def multiple_alpha_test():
    try:
        data = request.get_json()
        
        n_numbers = data.get('n_numbers', 100)
        n_intervals = data.get('n_intervals', 10)
        random_seed = data.get('random_seed', 42)
        
        alpha_values = [0.01, 0.05, 0.10]
        results = []
        
        for alpha in alpha_values:
            test = ChiSquareUniformityTest(n_numbers, n_intervals, alpha, random_seed)
            test_result = test.perform_chi_square_test()
            
            results.append({
                'alpha': alpha,
                'test_statistic': test_result['test_results']['chi_square'],
                'critical_value': test_result['test_results']['critical_value'],
                'p_value': test_result['test_results']['p_value'],
                'decision': test_result['test_results']['decision']
            })
        
        return jsonify({
            'success': True,
            'data': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/export-results', methods=['POST'])
def export_results():
    try:
        data = request.get_json()
        
        # Create a DataFrame for export
        df_data = []
        for row in data['frequency_table']:
            df_data.append({
                'Interval': row['interval'],
                'Range': row['range'],
                'Observed': row['observed'],
                'Expected': row['expected'],
                'O-E': row['O_minus_E'],
                '(O-E)²': row['O_minus_E_squared'],
                '(O-E)²/E': row['chi_component']
            })
        
        df = pd.DataFrame(df_data)
        
        # Add summary row
        summary_row = {
            'Interval': 'Total',
            'Range': '-',
            'Observed': sum([row['observed'] for row in data['frequency_table']]),
            'Expected': sum([row['expected'] for row in data['frequency_table']]),
            'O-E': '-',
            '(O-E)²': '-',
            '(O-E)²/E': data['test_results']['chi_square']
        }
        
        df = pd.concat([df, pd.DataFrame([summary_row])], ignore_index=True)
        
        return jsonify({
            'success': True,
            'csv_data': df.to_csv(index=False),
            'summary': {
                'test_statistic': data['test_results']['chi_square'],
                'critical_value': data['test_results']['critical_value'],
                'decision': data['test_results']['decision']
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True, port=5000)
