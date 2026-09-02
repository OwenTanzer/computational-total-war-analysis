# Result files

- `race_feature_triplets.csv`: the primary 24 × 54 representation.
- `race_feature_triplets_scaled.csv`: independently standardized columns.
- `race_feature_matrix_weighted.csv`: block- and triplet-weighted matrix used
  for distances and clustering.
- `race_feature_composites_0_100.csv`: interpretable feature and block summaries;
  these are relative to the 24-race sample, not absolute power ratings.
- `race_details.json`: unit counts and supporting per-race aggregation details.
- `clustering_report.json`: silhouette scores, Ward candidates, consensus labels,
  nearest neighbors, and the full co-clustering matrix.

The regenerable unit-level table is intentionally excluded from Git. Running
the study writes it to `work/race_feature_output/eligible_unit_scores.csv`.

