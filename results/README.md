# Accepted Benchmark Data

One accepted dataset per scenario is retained, totaling 42 controller runs. Original paths are preserved for configuration and provenance records.

| Scenario | Runs | Metrics |
|---|---:|---|
| Nominal tracking | 3 | [CSV](nominal/20260907T024619_815442Z/nominal_metrics.csv) |
| Unknown payload | 15 | [CSV](payload/20260911T014147_244577Z/payload_metrics.csv) |
| Controller-model error | 21 | [CSV](model_uncertainty/20260911T025328_299278Z/model_uncertainty_metrics.csv) |
| Endpoint force disturbance | 3 | [CSV](disturbance/20260913T114926_385587Z/disturbance_metrics.csv) |

Each run includes NPZ numerical histories, a YAML configuration, and JSON metadata. Each scenario includes its metric table, comparison figure, and frozen tuning snapshot. The shared [tuning record](tuning_search.json) contains the original 900 candidates and selected gains.

Historical metadata describes the original run environment and Git state, not the current checkout. Original data files are preserved byte for byte.

Benchmark scripts create new timestamped directories without replacing these accepted runs. New outputs are ignored by Git unless explicitly selected for publication.
