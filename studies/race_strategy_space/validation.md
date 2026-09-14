# Validation of the revised Janus diagnostics

The revision replaces coordinate-averaged membership error with total variation,
separates optimization repeatability, local robustness and structural stress,
and retains pole displacement and capability-profile changes.

Controlled tests cover padding-invariant membership movement, pole-label
permutations, translated poles with fixed memberships, degenerate references,
exact block-weight preservation, joint tolerance selection, exclusion of stress
from selection, convergence failures, and deterministic worker-count independence.

The source-backed gate compares all 24 x 54 original capability values to the
independent pre-refactor baseline. The regeneration gate compares all seven
reviewed files byte-for-byte in a separate output directory. Reviewed results
retain LF line endings under Windows checkout conversion.

Scientific tolerances are not adopted automatically. Conditional selections
in the result report depend jointly on membership reassignment and pole movement;
no adopted tolerance is a different state from failing an adopted tolerance.

## Completed verification

All 30 tests passed against the locked source; none skipped. A separate full rebuild matched all seven reviewed artifacts byte-for-byte. Worker-count independence also passed the controlled test. No scientific tolerance policy was adopted automatically.
