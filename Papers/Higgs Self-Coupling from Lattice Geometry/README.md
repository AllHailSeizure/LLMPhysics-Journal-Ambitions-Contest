# Higgs Self-Coupling from Lattice Geometry

**Author**: G. Partin  
**Prediction**: λ = 4/31 = 0.129032... (SM measured: 0.12938, error: 0.27%)

## Abstract

The Higgs boson self-coupling λ is the last fundamental parameter of the Standard Model not yet directly measured. We predict λ = 4/31 from the coordination-shell geometry of a 4D hypercubic lattice hosting the Klein-Gordon equation. The lattice vacuum stiffness χ₀ = 19 counts eigenvalue classes of the three-dimensional discrete Laplacian. On a D_st-dimensional hypercubic lattice, the first and second coordination numbers are z₁ = 2D_st and z₂ = 2D_st². The quartic self-coupling is determined by bond normalization and DC-mode exclusion at the second shell: λ = z₂/[z₁(z₂−1)] = D_st/(2D_st²−1). For D_st = 4: λ = 4/31 = 0.129032..., differing from the Standard Model tree-level value by only 0.27%. We present explicit falsification criteria testable at the High-Luminosity LHC during 2028-2030.

## Files

| File | Description |
|------|-------------|
| `paper_075_higgs_self_coupling.pdf` | Full manuscript (17 pages, 3 figures, 9 tables) |
| `reproduce_lambda_derivation.py` | **START HERE** — reproduces every algebraic claim (NumPy only) |
| `verify_lambda.py` | 100-digit precision verification (standard library only) |
| `mexican_hat_gov02_experiment.py` | Mexican hat V(χ) = λ(χ²−χ₀²)² dynamics test |
| `test_z2_universality.py` | Verifies formula holds for D_st = 2, 3, 4, 5 |
| `ergodicity_scaling_test.py` | Equipartition V_q/K ratio at 16³ and 32³ |
| `stability_boundary_experiment.py` | λ = 4/31 as resonance/stability boundary |
| `generate_figures.py` | Generates all three paper figures |
| `fig_*.pdf` | Pre-built figures |

## Quick Verification

```bash
pip install numpy  # only dependency
python reproduce_lambda_derivation.py
```

**Windows note**: If you see Unicode errors, set `$env:PYTHONIOENCODING="utf-8"` (PowerShell) or `set PYTHONIOENCODING=utf-8` (cmd) before running.

## Falsification Criteria

- **Strong**: HL-LHC measures λ/λ_SM outside [0.95, 1.05] → prediction falsified
- **Timeline**: Di-Higgs measurements expected 2028-2030

## Public Repository

All scripts also available at: https://github.com/gpartin/LFMPublicExperiments/tree/main/higgs_physics
