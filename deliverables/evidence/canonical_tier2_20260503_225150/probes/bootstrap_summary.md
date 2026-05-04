# Tier 2 Bootstrap CI Summary

- Evidence root: `deliverables/evidence/canonical_tier2_20260503_225150/`
- Source summary: `seed_aggregated_summary.md`
- Bootstrap unit: corruption seed
- Current usable seed count: `n_seeds=1` for every trainable corruption-stage probe row

## Readout

The bootstrap CI columns in `seed_aggregated_summary.md` currently equal the
point estimate for every numeric corruption-stage probe row. This is expected:
near-ceiling behavior makes 10 of 12 corruption source cells degenerate, leaving
only `control_corrupt_s2024` trainable for `corrupt_reward` and `neutral`.

These intervals should be presented as a reproducibility hook, not as evidence
of multi-seed uncertainty. A true seed-band claim requires at least two
trainable corruption seeds in the same `(base_stage, condition, layer)` cell.
