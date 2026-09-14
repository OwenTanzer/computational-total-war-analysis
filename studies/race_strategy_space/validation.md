# Janus validation and review notes

Validated against CTW commit
`8c2169b837288d03ba0188b468f06a2f3bcb4b28`, patch 8.1.1.

## Evidence

- All 24 tests passed; none skipped. The source-backed integration test ran.
- The independent pre-refactor baseline matched all 24 x 54 primary capability
  values within rtol=1e-10, atol=1e-12.
- Distance symmetry, zero diagonal, directional antisymmetry and the exact
  squared-distance decomposition passed.
- Convex-hull constraints, triangle reconstruction, deterministic optimization,
  label alignment, entropy versus uncertainty, duplicate-neighbor residuals,
  source rejection and unit-tier exclusion passed.
- A separate run rebuilt all seven reviewed artifacts in a fresh temporary
  output directory; exact file-set and byte comparison passed.
- Reviewed artifact paths enforce LF line endings so checkout conversion
  does not change the canonical result bytes.

## Scientific result and issue #5

The reconstruction-error knee is K=5 (relative squared error 0.466293110).
All K=3 through K=8 fail the explicitly fixed feature-resampling stability
thresholds. Therefore selected_resolution is null. The five-pole membership
table is explicitly provisional; it is available for theoretical inspection
without claiming stable archetypes have been established. The primary/unit-tier
distance correlation is 0.998456929.

This adds an explicit no-stable-resolution outcome to issue #5's selection rule.
The implementation is reviewable, but the issue should not be closed merely
because a membership table exists. The resampling protocol, analytical tolerances
and provisional interpretation need scientific review. Uncertainty also reflects
the seeded nonconvex optimizer's search; local convergence is not proof of a
global optimum.

## Reproduction

Use the commands in the repository README with a clean locked CTW checkout.
Set OPENBLAS_NUM_THREADS=1 and OMP_NUM_THREADS=1. Seeded byte reproduction
requires the same numerical-library environment; different floating-point
implementations can alter nonconvex optimization paths.
