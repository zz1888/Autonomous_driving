# Eval / Ability / Architecture Summary

Generated from `eval_results/Bench2Drive/**/res/merged.json` and `merged_ability.json`. Architecture fields for old anonymous folders are marked unknown when no reliable checkpoint/config link was available.

## Main Table

| eval_folder | DS | success_rate | route_score_avg | penalty_avg | completed_routes | failed_routes | ability_mean | ability_Overtaking | ability_Merging | ability_Emergency_Brake | ability_Give_Way | ability_Traffic_Signs | architecture | hist_len | previous_frame | added_heads | control_signal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026_05_13_13_24_08_simlingo_base_seed_42/seed_42 | 76.778 | 0.527 | 99.785 | 0.768 | 219 | 1 | 0.534 | 0.467 | 0.500 | 0.550 | 0.500 | 0.653 | old temporal gated-diff | 2 | Yes | Yes: target_speed + angle | target_speed + route |
| 2026_05_23_00_30_24_simlingo_base_seed_42_finetune_10ep_1e-5_cosine/seed_42 | 78.806 | 0.550 | 99.920 | 0.788 | 219 | 1 | 0.561 | 0.556 | 0.525 | 0.550 | 0.500 | 0.674 | old temporal gated-diff finetune | 2 | Yes | Yes: target_speed + angle | target_speed + route |
| 2026_05_23_00_30_24_simlingo_base_seed_42_finetune_10ep_1e-5_cosine_eval_stride5/seed_42 | 77.503 | 0.541 | 100.000 | 0.775 | 220 | 0 | 0.559 | 0.489 | 0.512 | 0.517 | 0.600 | 0.679 | old temporal gated-diff finetune + eval stride5 | 2 | Yes | Yes: target_speed + angle | target_speed + route |
| 2026_06_01_21_44_48_simlingo_base_seed_42_change_the_motion_resume_eval_motion_multi_head_stride5/seed_42 | 78.198 | 0.509 | 100.000 | 0.782 | 220 | 0 | 0.493 | 0.356 | 0.487 | 0.550 | 0.400 | 0.674 | motion-token temporal fusion | 2 | Yes | Yes: target_speed + angle; compact motion-token module | target_speed + route |
| seed_0 | 78.256 | 0.536 | 99.390 | 0.784 | 217 | 3 | 0.573 | 0.311 | 0.562 | 0.567 | 0.700 | 0.726 | historical baseline eval | unknown | unknown | unknown | unknown |
| seed_1 | 75.938 | 0.473 | 97.581 | 0.776 | 200 | 20 | 0.488 | 0.267 | 0.463 | 0.517 | 0.500 | 0.695 | historical baseline eval | unknown | unknown | unknown | unknown |
| seed_2 | 74.779 | 0.477 | 99.262 | 0.750 | 217 | 3 | 0.473 | 0.467 | 0.463 | 0.467 | 0.400 | 0.568 | historical baseline eval | unknown | unknown | unknown | unknown |
| seed_42 | 78.125 | 0.518 | 100.000 | 0.781 | 220 | 0 | 0.524 | 0.289 | 0.487 | 0.633 | 0.500 | 0.711 | single-frame target-speed baseline | 1 | No | Yes: target_speed + angle | target_speed + route |
| 2026_06_17_11_32_36_simlingo_base_seed_42_dinov2_l14_batch64_resume_eval_bench2drive220/seed_42 | 79.000 | 0.527 | 100.000 | 0.790 | 220 | 0 | 0.526 | 0.533 | 0.475 | 0.567 | 0.500 | 0.553 | DINOv2-L/14 K=8 | 2 | Yes | Yes: target_speed + angle; K=8 motion-token module | target_speed + route |
| 2026_06_20_20_24_52_simlingo_base_seed_42_dinov2_l14_safety_v13_finetune_10ep_eval_bench2drive220/seed_42 | 79.014 | 0.536 | 100.000 | 0.790 | 220 | 0 | 0.522 | 0.444 | 0.500 | 0.600 | 0.500 | 0.563 | DINOv2-L/14 K=16 safety FT | 2 | Yes | Yes: target_speed + angle; K=16 motion-token module | target_speed + route |
| 2026_06_20_20_24_52_simlingo_base_seed_42_dinov2_l14_safety_v13_finetune_10ep_waypoint_speed_seed42_eval_bench2drive220/seed_42 | 79.054 | 0.536 | 100.000 | 0.791 | 220 | 0 | 0.557 | 0.467 | 0.500 | 0.617 | 0.600 | 0.600 | DINOv2-L/14 K=16 safety FT, waypoint-speed control ablation | 2 | Yes | Yes: target_speed + angle; K=16 motion-token module | waypoint-derived speed + route |
| 2026_06_20_20_24_52_simlingo_base_seed_42_dinov2_l14_safety_v13_finetune_10ep_waypoint_speed_seed42_eval_bench2drive220_rerun/seed_42 | 81.437 | 0.568 | 100.000 | 0.814 | 220 | 0 | 0.564 | 0.556 | 0.512 | 0.650 | 0.500 | 0.600 | DINOv2-L/14 K=16 safety FT, waypoint-speed control rerun | 2 | Yes | Yes: target_speed + angle; K=16 motion-token module | waypoint-derived speed + route |

Ability values for waypoint-speed control rows use `Bench2Drive/tools/ability_benchmark.py` with a neutral fallback for Traffic Signs routes whose CARLA route interpolation does not expose a junction waypoint.

## Detailed Notes

### 2026_05_13_13_24_08_simlingo_base_seed_42/seed_42
- Checkpoint: `outputs/2026_05_13_13_24_08_simlingo_base_seed_42/checkpoints/last.ckpt`
- Temporal method: feat_curr + gate * (feat_curr - feat_prev)
- Notes: Old additive MotionGate; no compact motion token encoder.

### 2026_05_23_00_30_24_simlingo_base_seed_42_finetune_10ep_1e-5_cosine/seed_42
- Checkpoint: `outputs/2026_05_23_00_30_24_simlingo_base_seed_42_finetune_10ep_1e-5_cosine/checkpoints/last.ckpt`
- Temporal method: feat_curr + gate * (feat_curr - feat_prev)
- Notes: 10ep cosine finetune. Route 129 has manual rerun evidence from file mtimes.

### 2026_05_23_00_30_24_simlingo_base_seed_42_finetune_10ep_1e-5_cosine_eval_stride5/seed_42
- Checkpoint: `outputs/2026_05_23_00_30_24_simlingo_base_seed_42_finetune_10ep_1e-5_cosine/checkpoints/last.ckpt`
- Temporal method: feat_curr + gate * diff; eval samples t-5,t
- Notes: Same finetune checkpoint; eval temporal gap aligned by stride5.

### 2026_06_01_21_44_48_simlingo_base_seed_42_change_the_motion_resume_eval_motion_multi_head_stride5/seed_42
- Checkpoint: `outputs/2026_06_01_21_44_48_simlingo_base_seed_42_change_the_motion_resume/checkpoints/last.ckpt`
- Temporal method: diff -> LayerNorm/MLP -> avg pool K=8 motion tokens; concat with current tokens
- Notes: Latest motion multi-head eval; checkpoint confirmed motion_token_encoder and no old motion_gate.

### seed_0
- Checkpoint: `unknown`
- Temporal method: unknown
- Notes: Historical anonymous seed folder; config/checkpoint not reliably linked.

### seed_1
- Checkpoint: `unknown`
- Temporal method: unknown
- Notes: Historical anonymous seed folder; config/checkpoint not reliably linked.

### seed_2
- Checkpoint: `unknown`
- Temporal method: unknown
- Notes: Historical anonymous seed folder; config/checkpoint not reliably linked.

### seed_42
- Checkpoint: `likely outputs/2026_05_04_02_38_55_simlingo_base_seed_42/checkpoints/last.ckpt`
- Temporal method: None
- Notes: Checkpoint candidates around May 4 confirmed target_speed/angle heads and no motion modules.

### 2026_06_17_11_32_36_simlingo_base_seed_42_dinov2_l14_batch64_resume_eval_bench2drive220/seed_42
- Checkpoint: `outputs/2026_06_17_11_32_36_simlingo_base_seed_42_dinov2_l14_batch64_resume/checkpoints/last.ckpt`
- Temporal method: DINOv2-L/14 current tokens plus K=8 motion tokens.
- Notes: First DINOv2-L/14 full 220-route eval in the table.

### 2026_06_20_20_24_52_simlingo_base_seed_42_dinov2_l14_safety_v13_finetune_10ep_eval_bench2drive220/seed_42
- Checkpoint: `outputs/2026_06_20_20_24_52_simlingo_base_seed_42_dinov2_l14_safety_v13_finetune_10ep/checkpoints/last.ckpt`
- Temporal method: DINOv2-L/14 current tokens plus K=16 motion tokens.
- Notes: Safety-v13 finetune using target_speed + route control.

### 2026_06_20_20_24_52_simlingo_base_seed_42_dinov2_l14_safety_v13_finetune_10ep_waypoint_speed_seed42_eval_bench2drive220/seed_42
- Checkpoint: `outputs/2026_06_20_20_24_52_simlingo_base_seed_42_dinov2_l14_safety_v13_finetune_10ep/checkpoints/last.ckpt`
- Temporal method: DINOv2-L/14 current tokens plus K=16 learned motion tokens.
- Notes: Same trained model as V5 safety finetune; eval overrides control to use 1D waypoint-derived desired speed instead of `target_speed`.

### 2026_06_20_20_24_52_simlingo_base_seed_42_dinov2_l14_safety_v13_finetune_10ep_waypoint_speed_seed42_eval_bench2drive220_rerun/seed_42
- Checkpoint: `outputs/2026_06_20_20_24_52_simlingo_base_seed_42_dinov2_l14_safety_v13_finetune_10ep/checkpoints/last.ckpt`
- Temporal method: DINOv2-L/14 current tokens plus K=16 learned motion tokens.
- Notes: Same configuration as the waypoint-speed control ablation, rerun on 220 routes; highest observed DS so far.
