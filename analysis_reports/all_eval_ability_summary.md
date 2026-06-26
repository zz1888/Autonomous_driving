# All Evaluation, Ability, And Architecture Summary

| Run | Stage | Encoder | Hist | Heads | Temporal | Motion Tokens | Control | DS | RC | Penalty | Perfect | Ability | Overtaking | Merging | Emergency Brake | Give Way | Traffic Signs |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| seed_2 | V0 Vanilla base | LLaVA-Next | 1 | 2D waypoint | No | No | Waypoint-derived speed | 74.7787 | 99.26 | 0.7499 | 105 | 0.4729 | 0.4667 | 0.4625 | 0.4667 | 0.4000 | 0.5684 |
| seed_1 | V0 Vanilla base | LLaVA-Next | 1 | 2D waypoint | No | No | Waypoint-derived speed | 75.9378 | 97.58 | 0.7760 | 104 | 0.4881 | 0.2667 | 0.4625 | 0.5167 | 0.5000 | 0.6947 |
| 2026_05_13_13_24_08_simlingo_base_seed_42/seed_42 | V2 Temporal fusion | LLaVA-Next | 2 | 1D speed waypoint + target speed head | Yes, fused feature | No | target_speed + route | 76.7779 | 99.78 | 0.7679 | 116 | 0.5339 | 0.4667 | 0.5000 | 0.5500 | 0.5000 | 0.6526 |
| 2026_05_23_00_30_24_simlingo_base_seed_42_finetune_10ep_1e-5_cosine_eval_stride5/seed_42 | V2 Temporal finetune stride5 | LLaVA-Next | 2 | 1D speed waypoint + target speed head | Yes, fused feature; eval t-5,t | No | target_speed + route | 77.5031 | 100.00 | 0.7750 | 119 | 0.5594 | 0.4889 | 0.5125 | 0.5167 | 0.6000 | 0.6789 |
| seed_42 | V1 Direct control head | LLaVA-Next | 1 | 2D waypoint + target speed head | No | No | target_speed + route | 78.1246 | 100.00 | 0.7812 | 114 | 0.5240 | 0.2889 | 0.4875 | 0.6333 | 0.5000 | 0.7105 |
| 2026_06_01_21_44_48_simlingo_base_seed_42_change_the_motion_resume_eval_motion_multi_head_stride5/seed_42 | V3 Motion-token concat | LLaVA-Next | 2 | 1D speed waypoint + target speed head | Yes, motion tokens; eval t-5,t | Yes | target_speed + route | 78.1979 | 100.00 | 0.7820 | 112 | 0.4933 | 0.3556 | 0.4875 | 0.5500 | 0.4000 | 0.6737 |
| seed_0 | V1 Direct control head | LLaVA-Next | 1 | 2D waypoint + target speed head | No | No | target_speed + route | 78.2555 | 99.39 | 0.7841 | 118 | 0.5733 | 0.3111 | 0.5625 | 0.5667 | 0.7000 | 0.7263 |
| 2026_05_23_00_30_24_simlingo_base_seed_42_finetune_10ep_1e-5_cosine/seed_42 | V2 Temporal finetune | LLaVA-Next | 2 | 1D speed waypoint + target speed head | Yes, fused feature | No | target_speed + route | 78.8062 | 99.92 | 0.7882 | 121 | 0.5608 | 0.5556 | 0.5250 | 0.5500 | 0.5000 | 0.6737 |
| 2026_06_17_11_32_36_simlingo_base_seed_42_dinov2_l14_batch64_resume_eval_bench2drive220/seed_42 | V4 DINOv2-L/14 K=8 | DINOv2-L/14 | 2 | 1D speed waypoint + target speed head | Yes, K=8 motion tokens | Yes | target_speed + route | 79.0001 | 100.00 | 0.7900 | 116 | 0.5255 | 0.5333 | 0.4750 | 0.5667 | 0.5000 | 0.5526 |
| 2026_06_20_20_24_52_simlingo_base_seed_42_dinov2_l14_safety_v13_finetune_10ep_eval_bench2drive220/seed_42 | V5 DINOv2-L/14 K=16 safety FT | DINOv2-L/14 | 2 | 1D speed waypoint + target speed head | Yes, K=16 motion tokens | Yes | target_speed + route | 79.0135 | 100.00 | 0.7901 | 118 | 0.5215 | 0.4444 | 0.5000 | 0.6000 | 0.5000 | 0.5632 |
| 2026_06_20_20_24_52_simlingo_base_seed_42_dinov2_l14_safety_v13_finetune_10ep_waypoint_speed_seed42_eval_bench2drive220/seed_42 | V5 waypoint-speed control ablation | DINOv2-L/14 | 2 | 1D speed waypoint + target speed head | Yes, K=16 motion tokens | Yes | waypoint-derived speed + route | 79.0542 | 100.00 | 0.7905 | 118 | 0.5567 | 0.4667 | 0.5000 | 0.6167 | 0.6000 | 0.6000 |
| 2026_06_20_20_24_52_simlingo_base_seed_42_dinov2_l14_safety_v13_finetune_10ep_waypoint_speed_seed42_eval_bench2drive220_rerun/seed_42 | V5 waypoint-speed control rerun | DINOv2-L/14 | 2 | 1D speed waypoint + target speed head | Yes, K=16 motion tokens | Yes | waypoint-derived speed + route | 81.4365 | 100.00 | 0.8144 | 125 | 0.5636 | 0.5556 | 0.5125 | 0.6500 | 0.5000 | 0.6000 |

Ability values for the waypoint-speed control rows were computed with `Bench2Drive/tools/ability_benchmark.py` after adding a neutral fallback for Traffic Signs routes whose CARLA route interpolation does not expose a junction waypoint.

## Paths

- `seed_2`: `/home/mediacore/simlingo/eval_results/Bench2Drive/seed_2/res/merged.json`
- `seed_1`: `/home/mediacore/simlingo/eval_results/Bench2Drive/seed_1/res/merged.json`
- `2026_05_13_13_24_08_simlingo_base_seed_42/seed_42`: `/home/mediacore/simlingo/eval_results/Bench2Drive/2026_05_13_13_24_08_simlingo_base_seed_42/seed_42/res/merged.json`
- `2026_05_23_00_30_24_simlingo_base_seed_42_finetune_10ep_1e-5_cosine_eval_stride5/seed_42`: `/home/mediacore/simlingo/eval_results/Bench2Drive/2026_05_23_00_30_24_simlingo_base_seed_42_finetune_10ep_1e-5_cosine_eval_stride5/seed_42/res/merged.json`
- `seed_42`: `/home/mediacore/simlingo/eval_results/Bench2Drive/seed_42/res/merged.json`
- `2026_06_01_21_44_48_simlingo_base_seed_42_change_the_motion_resume_eval_motion_multi_head_stride5/seed_42`: `/home/mediacore/simlingo/eval_results/Bench2Drive/2026_06_01_21_44_48_simlingo_base_seed_42_change_the_motion_resume_eval_motion_multi_head_stride5/seed_42/res/merged.json`
- `seed_0`: `/home/mediacore/simlingo/eval_results/Bench2Drive/seed_0/res/merged.json`
- `2026_05_23_00_30_24_simlingo_base_seed_42_finetune_10ep_1e-5_cosine/seed_42`: `/home/mediacore/simlingo/eval_results/Bench2Drive/2026_05_23_00_30_24_simlingo_base_seed_42_finetune_10ep_1e-5_cosine/seed_42/res/merged.json`
- `2026_06_17_11_32_36_simlingo_base_seed_42_dinov2_l14_batch64_resume_eval_bench2drive220/seed_42`: `/home/mediacore/simlingo/eval_results/Bench2Drive/2026_06_17_11_32_36_simlingo_base_seed_42_dinov2_l14_batch64_resume_eval_bench2drive220/seed_42/res/merged.json`
- `2026_06_20_20_24_52_simlingo_base_seed_42_dinov2_l14_safety_v13_finetune_10ep_eval_bench2drive220/seed_42`: `/home/mediacore/simlingo/eval_results/Bench2Drive/2026_06_20_20_24_52_simlingo_base_seed_42_dinov2_l14_safety_v13_finetune_10ep_eval_bench2drive220/seed_42/res/merged.json`
- `2026_06_20_20_24_52_simlingo_base_seed_42_dinov2_l14_safety_v13_finetune_10ep_waypoint_speed_seed42_eval_bench2drive220/seed_42`: `/home/mediacore/simlingo/eval_results/Bench2Drive/2026_06_20_20_24_52_simlingo_base_seed_42_dinov2_l14_safety_v13_finetune_10ep_waypoint_speed_seed42_eval_bench2drive220/seed_42/res/merged.json`
- `2026_06_20_20_24_52_simlingo_base_seed_42_dinov2_l14_safety_v13_finetune_10ep_waypoint_speed_seed42_eval_bench2drive220_rerun/seed_42`: `/home/mediacore/simlingo/eval_results/Bench2Drive/2026_06_20_20_24_52_simlingo_base_seed_42_dinov2_l14_safety_v13_finetune_10ep_waypoint_speed_seed42_eval_bench2drive220_rerun/seed_42/res/merged.json`
