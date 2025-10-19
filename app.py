import os
from math import floor
from flask import Flask, request, jsonify, render_template
import scipy.stats as stats

BASE_DIR = os.path.dirname(__file__)
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))

# ---------- helpers ----------
def parse_numbers(s: str):
    """Parse comma/space/newline separated numbers into floats."""
    if not s or not str(s).strip():
        return []
    txt = str(s).replace("\n", " ").replace("\r", " ").replace("\t", " ").replace(";", " ")
    parts = []
    for chunk in txt.split(","):
        parts.extend(chunk.strip().split())
    out = []
    for p in parts:
        try:
            out.append(float(p))
        except:
            pass
    return out

def bin_counts(values, n_bins):
    """
    Count values into n equal-width bins on [0,1].
    Bin index = floor(x * n_bins); clamp last bin for x=1.0.
    """
    cnt = [0] * n_bins
    for x in values:
        if x < 0 or x > 1:
            # skip out-of-range
            continue
        idx = min(n_bins - 1, floor(x * n_bins))
        cnt[idx] += 1
    return cnt

# ---------- routes ----------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/calculate", methods=["POST"])
def calculate():
    data = request.get_json() or {}

    alpha = float(data.get("alpha", 0.05))
    n_bins = int(data.get("nBins", 10))

    raw_numbers_txt = data.get("rawNumbers", "").strip()
    observed = data.get("observed", [])
    expected = data.get("expected", [])

    steps = []
    table_rows = []

    # Mode A: raw numbers → auto-binning
    if raw_numbers_txt and not observed:
        values = parse_numbers(raw_numbers_txt)
        N = len(values)
        steps.append(f"Step 1: Read N = {N} numbers from input.")
        steps.append(f"Step 2: Choose number of classes (n) = {n_bins}.")
        # equal-width bins
        edges_desc = []
        for i in range(n_bins):
            left = i / n_bins
            right = (i + 1) / n_bins
            if i == 0:
                edges_desc.append(f"[{left:.1f}, {right:.1f}]")
            else:
                edges_desc.append(f"({left:.1f}, {right:.1f}]")
        steps.append("Step 3: Create equal-width bins on [0,1]: " + ", ".join(edges_desc))

        O = bin_counts(values, n_bins)
        steps.append(f"Step 4: Count observations per bin → Observed Oᵢ = {O}.")

        Ei = N / n_bins if n_bins > 0 else 0.0
        E = [Ei] * n_bins
        steps.append(f"Step 5: Expected for uniform distribution: Eᵢ = N/n = {N}/{n_bins} = {Ei:.4f} (same for all bins).")

    # Mode B: explicit observed & expected
    else:
        if len(observed) != len(expected):
            return jsonify({"error": "Observed and Expected must be the same length."}), 400
        O = [float(x) for x in observed]
        E = [float(x) for x in expected]
        n_bins = len(O)
        N = int(sum(O))
        steps.append(f"Step 1: Use provided Observed (Oᵢ) & Expected (Eᵢ) with n = {n_bins}.")
        steps.append(f"Oᵢ = {O}")
        steps.append(f"Eᵢ = {E}")
        steps.append(f"Step 2: Total N = ΣOᵢ = {N}")

    # Per-bin details (exactly n_bins rows)
    contrib, diff, sq = [], [], []
    for i in range(n_bins):
        oi, ei = O[i], E[i]
        di = oi - ei
        qi = di * di
        ci = (qi / ei) if ei > 0 else 0.0

        diff.append(di)
        sq.append(qi)
        contrib.append(ci)

        table_rows.append({
            "bin": i + 1,
            "upper": f"{(i + 1) / n_bins:.3f}",
            "observed": oi,
            "expected": ei,
            "O_minus_E": di,
            "(O_minus_E)^2": qi,
            "contribution": ci
        })

    steps.append("Step 3: Compute per-bin: (Oᵢ−Eᵢ), (Oᵢ−Eᵢ)², and contribution (Oᵢ−Eᵢ)²/Eᵢ.")
    chi2_stat = sum(contrib)
    df = max(n_bins - 1, 1)                   # ✅ df = n − 1
    critical = stats.chi2.ppf(1 - alpha, df)
    p_value = 1 - stats.chi2.cdf(chi2_stat, df)
    decision = "Reject H₀ (Not Uniform)" if chi2_stat >= critical else "Fail to Reject H₀ (Uniform)"

    steps.append(f"Step 4: χ² = Σ (Oᵢ−Eᵢ)²/Eᵢ = {chi2_stat:.6f}")
    steps.append(f"Step 5: Degrees of freedom df = n − 1 = {n_bins} − 1 = {df}")
    steps.append(f"Step 6: Critical value χ²(1−α, df) with α = {alpha} → {critical:.6f}")
    steps.append(f"Step 7: p-value = 1 − F_χ²(χ²; df) = {p_value:.6f}")
    steps.append(f"Decision: {decision}")

    return jsonify({
        "mode": "raw" if raw_numbers_txt and not observed else "explicit",
        "n": n_bins,
        "N": int(sum(O)),
        "alpha": alpha,
        "observed": O,
        "expected": E,
        "diff": diff,
        "squared": sq,
        "contribution": contrib,
        "chi2": chi2_stat,
        "df": df,
        "critical": critical,
        "p_value": p_value,
        "decision": decision,
        "steps": steps,
        "table": table_rows
    })

if __name__ == "__main__":
    app.run(debug=True)


