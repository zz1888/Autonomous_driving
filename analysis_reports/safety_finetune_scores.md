# Safety Finetune Evaluation Scores

Result folder:

`eval_results/Bench2Drive/2026_06_20_20_24_52_simlingo_base_seed_42_dinov2_l14_safety_v13_finetune_10ep_eval_bench2drive220/seed_42`

Architecture:

- DINOv2-L/14 encoder
- hist_len = 2
- motion tokens
- predict_control = true
- control signal = target speed + route
- safety v13 finetune, 10 epochs

## Main Bench2Drive Metrics

| Metric | Score |
|---|---:|
| Driving Score (DS) | 79.0135 |
| Route Completion (RC) | 100.0000 |
| Penalty Score | 0.7901 |
| Completed Routes | 220 / 220 |
| Failed Routes | 0 |
| Perfect Routes | 118 / 220 |

## Ability Benchmark

| Ability | Score |
|---|---:|
| Overtaking | 0.4444 |
| Merging | 0.5000 |
| Emergency Brake | 0.6000 |
| Give Way | 0.5000 |
| Traffic Signs | 0.5632 |
| Mean | 0.5215 |

## Efficiency / Smoothness Benchmark

Official script:

`Bench2Drive/tools/efficiency_smoothness_benchmark.py`

| Metric | Score |
|---|---:|
| Driving Efficiency | 255.1982 |
| Driving Smoothness | 0.3704 |

Note: metric logs contained 222 `metric_info.json` files for 220 merged records. Two stale retry/fault metric files were skipped by matching each route to metric length (`duration_game * 20` frames). Final alignment matched all 220 records.

## Infractions

| Infraction | Count |
|---|---:|
| min_speed_infractions | 3494 |
| collisions_vehicle | 96 |
| red_light | 25 |
| collisions_layout | 9 |
| outside_route_lanes | 9 |
| scenario_timeouts | 7 |
| collisions_pedestrian | 6 |
| yield_emergency_vehicle_infractions | 5 |
| stop_infraction | 4 |
| route_dev | 0 |
| vehicle_blocked | 0 |
| route_timeout | 0 |

## Waypoint-Speed Control Ablation

Same checkpoint, but eval control is forced to use 1D waypoint-derived desired speed instead of the direct `target_speed` head.

Result folder:

`eval_results/Bench2Drive/2026_06_20_20_24_52_simlingo_base_seed_42_dinov2_l14_safety_v13_finetune_10ep_waypoint_speed_seed42_eval_bench2drive220/seed_42`

### Main Bench2Drive Metrics

| Metric | Target-Speed Control | Waypoint-Speed Control |
|---|---:|---:|
| Driving Score (DS) | 79.0135 | **79.0542** |
| Route Completion (RC) | 100.0000 | 100.0000 |
| Penalty Score | 0.7901 | **0.7905** |
| Completed Routes | 220 / 220 | 220 / 220 |
| Failed Routes | 0 | 0 |
| Perfect Routes | 118 / 220 | 118 / 220 |

### Ability Benchmark

| Ability | Target-Speed Control | Waypoint-Speed Control |
|---|---:|---:|
| Overtaking | 0.4444 | **0.4667** |
| Merging | 0.5000 | 0.5000 |
| Emergency Brake | 0.6000 | **0.6167** |
| Give Way | 0.5000 | **0.6000** |
| Traffic Signs | **0.5632** | 0.4632 |
| Mean | 0.5215 | **0.5293** |

Note: waypoint-speed ability is computed with the offline ability script variant. It uses the same scenario groups and infraction-based success rule, but does not run CARLA to apply the extra Traffic Signs junction-completion check in the official Bench2Drive script.

### Efficiency / Smoothness Benchmark

| Metric | Waypoint-Speed Control |
|---|---:|
| Driving Efficiency | 233.6209 |
| Driving Smoothness | 0.3135 |

Interpretation: waypoint-speed control slightly improves DS and emergency/give-way ability, but it weakens Traffic Signs behavior. This supports a future hybrid controller: waypoint-derived speed for geometry/horizon behavior, with target-speed override for red lights, signalized junctions, and stop/go interactions.
