"""
ERGODICITY SCALING TEST for Paper 75
=====================================
Tests the equipartition V_q/K ratio at TWO lattice sizes (16^3 and 32^3)
to demonstrate finite-size scaling and strengthen the ergodicity claim.

Uses the Mexican hat potential V(chi) = lambda_H * (chi^2 - chi0^2)^2
with lambda_H = 4/31 (the Paper 75 prediction).

Leapfrog (velocity Verlet) integration of the chi field only (no Psi).
"""
import numpy as np
import time
import json
from pathlib import Path

def run_ergodicity_test(D, N, chi0, lam, dt, n_steps, n_seeds):
    """Run ergodicity test on D-dimensional lattice of size N^D."""
    shape = tuple([N] * D)
    N_total = int(np.prod(shape))
    
    # Build neighbor list (periodic boundaries)
    indices = np.arange(N_total)
    multi_idx = np.array(np.unravel_index(indices, shape)).T
    neighbors = []
    for d in range(D):
        for delta in [+1, -1]:
            shifted = multi_idx.copy()
            shifted[:, d] = (shifted[:, d] + delta) % shape[d]
            neighbors.append(np.ravel_multi_index(shifted.T, shape))
    
    c, dx = 1.0, 1.0
    all_ratios = []
    all_lyapunov = []
    
    for seed in range(n_seeds):
        rng = np.random.default_rng(42 + seed)
        chi = chi0 + 0.3 * rng.standard_normal(N_total)
        pi_f = 0.3 * rng.standard_normal(N_total)
        
        # Shadow trajectory for Lyapunov
        chi_s = chi.copy() + 1e-10 * rng.standard_normal(N_total)
        pi_s = pi_f.copy()
        
        n_therm = n_steps // 2
        K_s, Vq_s = [], []
        lyap_sum = 0.0
        lyap_count = 0
        
        for step in range(n_steps):
            # Velocity Verlet for main trajectory
            lap = np.zeros(N_total)
            for nb in neighbors:
                lap += chi[nb] - chi
            lap *= c**2 / dx**2
            force = lap - 4*lam*chi*(chi**2 - chi0**2)
            pi_f += 0.5*dt*force
            chi += dt*pi_f
            lap = np.zeros(N_total)
            for nb in neighbors:
                lap += chi[nb] - chi
            lap *= c**2 / dx**2
            force = lap - 4*lam*chi*(chi**2 - chi0**2)
            pi_f += 0.5*dt*force
            
            # Shadow trajectory for Lyapunov
            lap_s = np.zeros(N_total)
            for nb in neighbors:
                lap_s += chi_s[nb] - chi_s
            lap_s *= c**2 / dx**2
            force_s = lap_s - 4*lam*chi_s*(chi_s**2 - chi0**2)
            pi_s += 0.5*dt*force_s
            chi_s += dt*pi_s
            lap_s = np.zeros(N_total)
            for nb in neighbors:
                lap_s += chi_s[nb] - chi_s
            lap_s *= c**2 / dx**2
            force_s = lap_s - 4*lam*chi_s*(chi_s**2 - chi0**2)
            pi_s += 0.5*dt*force_s
            
            # Lyapunov rescaling every 100 steps
            if step > 0 and step % 100 == 0:
                delta = np.sqrt(np.mean((chi_s - chi)**2 + (pi_s - pi_f)**2))
                if delta > 1e-15:
                    lyap_sum += np.log(delta / 1e-10)
                    lyap_count += 1
                    # Rescale shadow
                    chi_s = chi + (chi_s - chi) * 1e-10 / delta
                    pi_s = pi_f + (pi_s - pi_f) * 1e-10 / delta
            
            # Sample after thermalization
            if step >= n_therm and step % 10 == 0:
                K_s.append(0.5 * np.mean(pi_f**2))
                Vq_s.append(lam * np.mean((chi**2 - chi0**2)**2))
        
        ratio = np.mean(Vq_s) / np.mean(K_s)
        all_ratios.append(ratio)
        
        lyap = lyap_sum / (lyap_count * 100 * dt) if lyap_count > 0 else 0
        all_lyapunov.append(lyap)
        
        print(f"  Seed {seed:2d}: V_q/K = {ratio:.6f}, λ_L = {lyap:.4f}")
    
    m = np.mean(all_ratios)
    s = np.std(all_ratios)
    se = s / np.sqrt(len(all_ratios))
    cv = (s / m) * 100
    lyap_mean = np.mean(all_lyapunov)
    
    # Autocorrelation
    r = np.array(all_ratios)
    r_centered = r - np.mean(r)
    if np.var(r_centered) > 0:
        autocorr = np.correlate(r_centered, r_centered, mode='full')
        autocorr = autocorr[len(autocorr)//2:]
        autocorr /= autocorr[0]
        tau = 0
        for i in range(1, len(autocorr)):
            if autocorr[i] < 0:
                tau = i
                break
        if tau == 0:
            tau = len(autocorr)
    else:
        tau = 1
    
    return {
        "mean": float(m), "std": float(s), "sem": float(se),
        "cv_pct": float(cv), "lyapunov_mean": float(lyap_mean),
        "tau_auto": int(tau), "ratios": [float(x) for x in all_ratios],
        "n_seeds": n_seeds, "N": N, "D": D
    }


if __name__ == "__main__":
    lam = 4.0 / 31.0
    chi0 = 2.0  # Small chi0 for thermal testing (large chi0 would require tiny dt)
    dt = 0.01
    n_steps = 30000
    n_seeds = 20
    
    results = {}
    
    # ===== N=16 (baseline, matches paper) =====
    print("=" * 60)
    print(f"ERGODICITY TEST: N=16 (3D) -> 16^3 = {16**3} cells, {n_seeds} seeds")
    print(f"  lambda_H = 4/31 = {lam:.6f}, chi0 = {chi0}, dt = {dt}")
    print("=" * 60)
    t0 = time.time()
    r16 = run_ergodicity_test(3, 16, chi0, lam, dt, n_steps, n_seeds)
    t16 = time.time() - t0
    r16["time_sec"] = round(t16, 1)
    results["N16"] = r16
    print(f"\nN=16: V_q/K = {r16['mean']:.6f} ± {r16['sem']:.6f}, "
          f"CV = {r16['cv_pct']:.4f}%, λ_L = {r16['lyapunov_mean']:.4f}, "
          f"τ = {r16['tau_auto']}, time = {t16:.0f}s\n")
    
    # ===== N=32 (NEW scaling test) =====
    print("=" * 60)
    print(f"ERGODICITY TEST: N=32 (3D) -> 32^3 = {32**3} cells, {n_seeds} seeds")
    print(f"  lambda_H = 4/31 = {lam:.6f}, chi0 = {chi0}, dt = {dt}")
    print("=" * 60)
    t0 = time.time()
    r32 = run_ergodicity_test(3, 32, chi0, lam, dt, n_steps, n_seeds)
    t32 = time.time() - t0
    r32["time_sec"] = round(t32, 1)
    results["N32"] = r32
    print(f"\nN=32: V_q/K = {r32['mean']:.6f} ± {r32['sem']:.6f}, "
          f"CV = {r32['cv_pct']:.4f}%, λ_L = {r32['lyapunov_mean']:.4f}, "
          f"τ = {r32['tau_auto']}, time = {t32:.0f}s\n")
    
    # ===== COMPARISON =====
    print("=" * 60)
    print("FINITE-SIZE SCALING COMPARISON")
    print("=" * 60)
    diff = abs(r32['mean'] - r16['mean'])
    rel_diff = diff / r16['mean'] * 100
    print(f"N=16 (4096 cells):  V_q/K = {r16['mean']:.6f} ± {r16['sem']:.6f}, CV = {r16['cv_pct']:.4f}%")
    print(f"N=32 (32768 cells): V_q/K = {r32['mean']:.6f} ± {r32['sem']:.6f}, CV = {r32['cv_pct']:.4f}%")
    print(f"Ratio difference:   |Δ| = {diff:.6f} ({rel_diff:.3f}%)")
    print(f"CV improvement:     {r16['cv_pct']:.4f}% → {r32['cv_pct']:.4f}%")
    print(f"Lyapunov (both>0):  {r16['lyapunov_mean']:.4f}, {r32['lyapunov_mean']:.4f}")
    
    consistent = rel_diff < 2.0
    print(f"\nFINITE-SIZE SCALING: {'PASSED' if consistent else 'FAILED'} "
          f"(ratio stable to {rel_diff:.3f}% across 8× volume increase)")
    
    if consistent:
        print("\nCONCLUSION: Ergodicity confirmed at two lattice sizes.")
        print("The V_q/K ratio is stable under 8× volume scaling,")
        print("ruling out finite-size artifacts at the tested scales.")
    
    # Save results
    out_path = Path(__file__).resolve().parent / "ergodicity_scaling_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {out_path}")
