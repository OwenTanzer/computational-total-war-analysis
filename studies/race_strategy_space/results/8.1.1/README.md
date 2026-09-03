# Result files

- `race_feature_triplets.csv`: the primary 24 × 69 representation, retaining
  `access` for multiplayer cost and adding `campaign_access` for unit-tier
  progression.
- `race_feature_triplets_scaled.csv`: independently standardized columns.
- `race_feature_matrix_weighted.csv`: block- and view-weighted matrix used
  for distances and clustering.
- `race_feature_matrix_weighted_cost_only.csv`: 54-dimensional sensitivity
  matrix excluding campaign access.
- `race_feature_composites_0_100.csv`: interpretable feature and block summaries;
  these are relative to the 24-race sample, not absolute power ratings.
- `race_feature_composites_cost_only_0_100.csv`: sensitivity composites using
  multiplayer-cost access alone.
- `race_details.json`: unit counts and supporting per-race aggregation details.
- `clustering_report.json`: silhouette scores, Ward candidates, consensus labels,
  nearest neighbors, and the full co-clustering matrix.
- `clustering_report_cost_only.json`: matching sensitivity report without the
  campaign-access columns.

The regenerable unit-level table is intentionally excluded from Git. Running
the study writes it to `work/race_feature_output/eligible_unit_scores.csv`.
