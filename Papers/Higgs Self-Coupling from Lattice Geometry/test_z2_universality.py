"""
EXPERIMENT: Multi-Dimensional z2 Universality Test
====================================================

HYPOTHESIS: The Higgs self-coupling formula λ_H = D_st / (2*D_st² - 1)
holds for ALL spacetime dimensions D_st = 2, 3, 4, 5, not just D_st = 4.

METHOD: For each D_st, simulate the Mexican hat Hamiltonian on a
D_st-dimensional periodic lattice. Measure the equilibrium ratio
V_quartic / K_kinetic. If equipartition holds with the predicted λ,
this ratio should be approximately 1.0.

Additionally, for each D_st we SCAN λ values to find the one that
gives V_q/K ≈ 1.0 (the "measured" coupling), and compare with the
z2 prediction λ = D_st/(2*D_st²-1).

This test is the decisive evidence for the numerator = D_st conjecture.
"""

import numpy as np
from itertools import product
import time

def create_lattice(D, N):
    """Create a D-dimensional periodic lattice with N points per side."""
    shape = tuple([N] * D)
    return shape

def get_neighbors(shape):
    """Precompute neighbor indices for a D-dimensional periodic lattice."""
    D = len(shape)
    N_total = int(np.prod(shape))
    
    # For each dimension, compute +1 and -1 neighbor shifts
    neighbors = []  # list of (N_total,) arrays, one per neighbor direction
    
    indices = np.arange(N_total)
    multi_idx = np.array(np.unravel_index(indices, shape)).T  # (N_total, D)
    
    for d in range(D):
        for delta in [+1, -1]:
            shifted = multi_idx.copy()
            shifted[:, d] = (shifted[:, d] + delta) % shape[d]
            flat_shifted = np.ravel_multi_index(shifted.T, shape)
            neighbors.append(flat_shifted)
    
    return neighbors  # 2*D arrays, each of length N_total


def simulate_mexican_hat(D_st, N, lam, chi0, n_steps, dt, n_seeds=5):
    """
    Simulate Mexican hat Hamiltonian in D_st dimensions.
    
    H = sum_x [ (1/2) pi^2 + (c^2/2) sum_mu (chi(x+mu) - chi(x))^2 + lam*(chi^2 - chi0^2)^2 ]
    
    Hamilton's equations:
        d(chi)/dt = pi
        d(pi)/dt = c^2 * Lap(chi) - 4*lam*chi*(chi^2 - chi0^2)
    
    Returns V_quartic/K_kinetic ratio averaged over seeds.
    """
    c = 1.0
    dx = 1.0
    shape = create_lattice(D_st, N)
    N_total = int(np.prod(shape))
    neighbors = get_neighbors(shape)
    z1 = 2 * D_st  # first coordination number
    
    ratios = []
    
    for seed in range(n_seeds):
        rng = np.random.default_rng(42 + seed)
        
        # Initialize near vacuum chi0 with small thermal fluctuations
        chi = chi0 + 0.3 * rng.standard_normal(N_total)
        pi_field = 0.3 * rng.standard_normal(N_total)  # conjugate momentum
        
        # Thermalization
        n_therm = n_steps // 2
        
        K_samples = []
        Vq_samples = []
        
        for step in range(n_steps):
            # Leapfrog integration
            # Half step momentum
            lap_chi = np.zeros(N_total)
            for nb in neighbors:
                lap_chi += chi[nb] - chi
            lap_chi *= c**2 / dx**2
            
            force = lap_chi - 4 * lam * chi * (chi**2 - chi0**2)
            pi_field += 0.5 * dt * force
            
            # Full step position
            chi += dt * pi_field
            
            # Half step momentum
            lap_chi = np.zeros(N_total)
            for nb in neighbors:
                lap_chi += chi[nb] - chi
            lap_chi *= c**2 / dx**2
            
            force = lap_chi - 4 * lam * chi * (chi**2 - chi0**2)
            pi_field += 0.5 * dt * force
            
            # Measure after thermalization
            if step >= n_therm and step % 10 == 0:
                K = 0.5 * np.mean(pi_field**2)
                Vq = lam * np.mean((chi**2 - chi0**2)**2)
                K_samples.append(K)
                Vq_samples.append(Vq)
        
        if len(K_samples) > 10:
            ratio = np.mean(Vq_samples) / np.mean(K_samples)
            ratios.append(ratio)
    
    return np.mean(ratios), np.std(ratios) / np.sqrt(len(ratios))


def scan_lambda(D_st, N, chi0, n_steps, dt, n_seeds, lam_values):
    """Scan lambda values and find where V_q/K = 1.0."""
    results = []
    for lam in lam_values:
        ratio, err = simulate_mexican_hat(D_st, N, lam, chi0, n_steps, dt, n_seeds)
        results.append((lam, ratio, err))
    return results


def main():
    print("=" * 70)
    print("MULTI-DIMENSIONAL z2 UNIVERSALITY TEST")
    print("Testing: lambda_H = D_st / (2*D_st^2 - 1)")
    print("=" * 70)
    print()
    
    chi0 = 2.0  # Use smaller chi0 for computational efficiency (formula is chi0-independent)
    dt = 0.01
    
    # Configuration per dimension (balance accuracy vs speed)
    configs = {
        2: {"N": 32, "n_steps": 40000, "n_seeds": 10},
        3: {"N": 12, "n_steps": 30000, "n_seeds": 8},
        4: {"N": 6,  "n_steps": 20000, "n_seeds": 6},
        5: {"N": 4,  "n_steps": 20000, "n_seeds": 6},
    }
    
    print(f"{'D_st':>4} | {'z2':>4} | {'z2-1':>5} | {'Predicted λ':>12} | {'Measured V_q/K':>14} | {'Status':>8}")
    print("-" * 70)
    
    all_results = []
    
    for D_st in [2, 3, 4, 5]:
        cfg = configs[D_st]
        lam_predicted = D_st / (2 * D_st**2 - 1)
        z2 = 2 * D_st**2
        
        t0 = time.time()
        ratio, err = simulate_mexican_hat(
            D_st, cfg["N"], lam_predicted, chi0,
            cfg["n_steps"], dt, cfg["n_seeds"]
        )
        elapsed = time.time() - t0
        
        # V_q/K should be ≈ 1.0 if lambda is correct
        status = "PASS" if abs(ratio - 1.0) < 0.15 else "FAIL"
        
        print(f"{D_st:>4} | {z2:>4} | {z2-1:>5} | {lam_predicted:>12.6f} | {ratio:>10.4f} ± {err:.4f} | {status:>8}  ({elapsed:.1f}s)")
        
        all_results.append({
            "D_st": D_st, "z2": z2, "lambda_pred": lam_predicted,
            "Vq_K_ratio": ratio, "Vq_K_err": err, "status": status
        })
    
    print()
    print("=" * 70)
    print("LAMBDA SCAN: Find measured λ independently at each D_st")
    print("=" * 70)
    print()
    
    # For each D_st, scan lambda values near the prediction to find V_q/K = 1.0
    scan_results = []
    
    for D_st in [2, 3, 4, 5]:
        cfg = configs[D_st]
        lam_pred = D_st / (2 * D_st**2 - 1)
        
        # Scan range: predicted ± 50%
        lam_low = lam_pred * 0.5
        lam_high = lam_pred * 1.5
        lam_values = np.linspace(lam_low, lam_high, 7)
        
        t0 = time.time()
        results = scan_lambda(D_st, cfg["N"], chi0, cfg["n_steps"], dt, cfg["n_seeds"], lam_values)
        elapsed = time.time() - t0
        
        # Find λ where V_q/K is closest to 1.0
        best = min(results, key=lambda r: abs(r[1] - 1.0))
        lam_measured = best[0]
        
        # Linear interpolation between the two points bracketing V_q/K = 1.0
        for i in range(len(results) - 1):
            r1, r2 = results[i], results[i+1]
            if (r1[1] - 1.0) * (r2[1] - 1.0) < 0:
                # Linear interpolation
                f = (1.0 - r1[1]) / (r2[1] - r1[1])
                lam_measured = r1[0] + f * (r2[0] - r1[0])
                break
        
        error_pct = abs(lam_measured - lam_pred) / lam_pred * 100
        
        # Also test alternative numerators
        lam_alt_1 = 1 / (2 * D_st**2 - 1)          # numerator = 1
        lam_alt_C2 = D_st*(D_st-1)/2 / (2*D_st**2 - 1)  # numerator = C(D_st,2)
        lam_alt_2D = 2*D_st / (2 * D_st**2 - 1)    # numerator = 2*D_st
        
        scan_results.append({
            "D_st": D_st,
            "lambda_pred": lam_pred,
            "lambda_measured": lam_measured,
            "error_pct": error_pct,
            "alt_1": lam_alt_1,
            "alt_C2": lam_alt_C2,
            "alt_2D": lam_alt_2D,
        })
        
        print(f"D_st = {D_st}: λ_predicted = {lam_pred:.6f}, λ_measured = {lam_measured:.6f} (error: {error_pct:.1f}%)  ({elapsed:.1f}s)")
        print(f"         Alt numerators: N=1 → {lam_alt_1:.6f}, N=C(D,2) → {lam_alt_C2:.6f}, N=2D → {lam_alt_2D:.6f}")
    
    print()
    print("=" * 70)
    print("SUMMARY TABLE (for paper)")
    print("=" * 70)
    print()
    print(f"{'D_st':>4} | {'z2':>4} | {'Predicted':>10} | {'Measured':>10} | {'Error':>7} | {'N=1':>8} | {'N=C(D,2)':>10} | {'N=2D':>8}")
    print("-" * 80)
    for r in scan_results:
        print(f"{r['D_st']:>4} | {2*r['D_st']**2:>4} | {r['lambda_pred']:>10.6f} | {r['lambda_measured']:>10.6f} | {r['error_pct']:>5.1f}% | {r['alt_1']:>8.6f} | {r['alt_C2']:>10.6f} | {r['alt_2D']:>8.6f}")
    
    print()
    
    # Final verdict
    all_pass = all(r["error_pct"] < 15 for r in scan_results)
    print("=" * 70)
    print(f"VERDICT: {'ALL DIMENSIONS CONFIRM λ = D_st/(2D_st²-1)' if all_pass else 'SOME DIMENSIONS FAILED'}")
    print("=" * 70)
    
    if all_pass:
        print()
        print("The z₂ formula λ_H = D_st/(2D_st²−1) is confirmed at D_st = 2, 3, 4, 5.")
        print("The numerator = D_st is not a coincidence at D_st = 4.")
        print("It is a universal pattern verified across multiple dimensions.")


if __name__ == "__main__":
    main()
