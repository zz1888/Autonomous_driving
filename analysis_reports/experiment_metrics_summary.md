# Experiment Metrics Summary

Generated from local Bench2Drive evaluation outputs.

| Method | Train | Input | DS | SR (%) | Ability Mean | Driving Efficiency | Driving Smoothness | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| My Method | IL | C | 74.78 | 47.73 | 0.4729 | N/A | N/A | `seed_2` has no saved `metric_info.json`, so efficiency/smoothness cannot be recomputed offline. |
| My Method V2 (direct head) | IL | C | 78.12 | 51.82 | 0.5240 | 246.3310 | 0.3912 | Computed from 220 metric files. |
| My Method V3 (temporal fusion) | IL | C | 76.78 | 52.73 | 0.5339 | 241.4440 | 0.3459 | Computed from 220 matched metric files; raw folder contains rerun leftovers. |
| My Method V4 (motion 8 tokens concat) | IL | C | 78.20 | 50.91 | 0.4933 | 240.6914 | 0.3054 | Computed from 220 matched metric files; raw folder contains one extra metric file. |
| My Method V5 (DINOv2 K=16 target-speed) | IL | C | 79.01 | 53.64 | 0.5215 | 255.1982 | 0.3704 | DINOv2-L/14, K=16 motion tokens, safety v13 finetune, target_speed + route control. Metric folder had 222 files for 220 records, with 2 retry/fault leftovers excluded by timestamp matching. |
| My Method V6 (DINOv2 K=16 waypoint-speed) | IL | C | 79.05 | 53.64 | 0.5567 | 233.6209 | 0.3135 | Same V5 checkpoint, eval control uses 1D waypoint-derived speed + route. |
| My Method V6 rerun (DINOv2 K=16 waypoint-speed) | IL | C | 81.44 | 56.82 | 0.5636 | 231.9046 | 0.3215 | Same V6 setup rerun; highest observed DS. Metric folder had 223 files for 220 records, with 3 retry/fault leftovers excluded by timestamp matching. |

## Source Files

| Method | Merged Result |
|---|---|
| My Method | `eval_results/Bench2Drive/seed_2/res/merged.json` |
| My Method V2 (direct head) | `eval_results/Bench2Drive/seed_42/res/merged.json` |
| My Method V3 (temporal fusion) | `eval_results/Bench2Drive/2026_05_13_13_24_08_simlingo_base_seed_42/seed_42/res/merged.json` |
| My Method V4 (motion 8 tokens concat) | `eval_results/Bench2Drive/2026_06_01_21_44_48_simlingo_base_seed_42_change_the_motion_resume_eval_motion_multi_head_stride5/seed_42/res/merged.json` |
| My Method V5 (DINOv2 K=16 target-speed) | `eval_results/Bench2Drive/2026_06_20_20_24_52_simlingo_base_seed_42_dinov2_l14_safety_v13_finetune_10ep_eval_bench2drive220/seed_42/res/merged.json` |
| My Method V6 (DINOv2 K=16 waypoint-speed) | `eval_results/Bench2Drive/2026_06_20_20_24_52_simlingo_base_seed_42_dinov2_l14_safety_v13_finetune_10ep_waypoint_speed_seed42_eval_bench2drive220/seed_42/res/merged.json` |
| My Method V6 rerun (DINOv2 K=16 waypoint-speed) | `eval_results/Bench2Drive/2026_06_20_20_24_52_simlingo_base_seed_42_dinov2_l14_safety_v13_finetune_10ep_waypoint_speed_seed42_eval_bench2drive220_rerun/seed_42/res/merged.json` |

## Repro Notes

Efficiency and smoothness were computed with:

```bash
python Bench2Drive/tools/efficiency_smoothness_benchmark.py -f <merged.json> -m <metric_index_dir>
```

The original metric folders are timestamp-based, while the Bench2Drive tool expects `metric_dir/<save_name>/metric_info.json`. Temporary symlink indexes were built under `/tmp` by matching each route `save_name` timestamp to the nearest saved metric timestamp. Ability uses the Bench2Drive script with a neutral fallback for routes whose Traffic Signs extra junction check cannot find a CARLA junction waypoint.
