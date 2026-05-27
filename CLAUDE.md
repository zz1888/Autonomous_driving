# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SimLingo is a Vision-Language-Action (VLA) model for autonomous driving in CARLA, accepted as a CVPR 2025 highlight. It combines vision-only closed-loop driving with language capabilities (VQA, commentary, instruction following) via "Action Dreaming."

## Environment Setup

```bash
conda env create -f environment.yaml
conda activate simlingo
pip install torch==2.2.0
pip install flash-attn==2.7.0.post2
bash setup_carla.sh
```

Required environment variables (add to shell profile):
```bash
export CARLA_ROOT=/path/to/CARLA/root
export WORK_DIR=/path/to/simlingo
export PYTHONPATH=$PYTHONPATH:${CARLA_ROOT}/PythonAPI/carla
export SCENARIO_RUNNER_ROOT=${WORK_DIR}/scenario_runner
export LEADERBOARD_ROOT=${WORK_DIR}/leaderboard
export PYTHONPATH="${CARLA_ROOT}/PythonAPI/carla/":"${SCENARIO_RUNNER_ROOT}":"${LEADERBOARD_ROOT}":${PYTHONPATH}
```

## Training Commands

**SimLingo-Base** (vision-only, ~235M LLM, LLaVA-Next encoder):
```bash
python simlingo_base_training/train.py experiment=simlingo_base_1 data_module.batch_size=8 gpus=8
```

**SimLingo** (full model with language, InternVL2-1B + LoRA):
```bash
python simlingo_training/train.py experiment=simlingo_seed1 data_module.batch_size=8 gpus=8
```

For SLURM cluster: `train_simlingo_seed1.sh` is a pre-configured SLURM script.

Debug runs use `experiment=debug` which overrides to smaller batch/fewer steps.

## Evaluation Commands

**Bench2Drive closed-loop evaluation** (launches SLURM jobs per route):
```bash
python start_eval_simlingo.py
```

**Language evaluation** (QA, commentary, dreaming predictions):
```bash
python simlingo_training/eval.py
python simlingo_training/eval_metrics.py  # computes metrics via GPT-4
```

## Architecture

The system has three tiers:

### 1. Inference Agent (`team_code/agent_simlingo.py`)
`LingoAgent` implements the CARLA agent interface. It loads the trained model, processes multi-camera sensor data, runs model inference, and converts outputs (waypoints + speed) to control signals via PID controllers. UKF filtering smooths predicted trajectories.

### 2. Two Model Variants

**SimLingo-Base** (`simlingo_base_training/`):
- Vision encoder: LLaVA-Next (frozen backbone + projection layer), outputs downsampled feature grid
- LLM: Custom small Llama (tiny=50M to large=1.1B, default x-small=235M)
- Outputs: waypoints + speed only (no language generation)

**SimLingo** (`simlingo_training/`):
- Vision encoder: InternVL2-1B (frozen + MLP projection), multi-scale features
- LLM: InternVL2-1B fine-tuned with LoRA (rank=32, alpha=64)
- Outputs: waypoints + speed + language (VQA answers, commentary, action dreaming)

Both variants are `DrivingModel` (PyTorch Lightning `LightningModule`) in their respective `models/driving.py`. Input adaptors in `models/adaptors/adaptors.py` handle route tokens and speed encoding.

### 3. Data Pipeline

Three dataset types in `simlingo_training/dataloader/`:
- `dataset_driving.py` — expert driving trajectories from CARLA
- `dataset_dreamer.py` — language instruction + future trajectory pairs ("Action Dreaming")
- `dataset_eval_qa_comm.py` / `dataset_eval_dreamer.py` — evaluation datasets

The `DataModule` uses weighted bucketed sampling across scenario types. Buckets are defined in `config/data_module/carla_bucket_v12_dreamer.yaml`. Raw data lives in `database/simlingo/`, bucket indices in `database/bucketsv2_simlingo/`.

## Configuration System

Uses **Hydra 1.3.2** with hierarchical YAML configs. Entry point is `config/config.yaml`, overridden by `experiment/` configs. Key overrideable fields:
- `experiment=simlingo_seed1` — selects experiment config
- `data_module.batch_size=8` — data loading settings
- `gpus=8` — number of GPUs

Config dataclasses are defined in each module's `config.py` (e.g., `simlingo_training/config.py`). Outputs go to `outputs/<timestamp>_<experiment_name>/`.

## Key File Locations

| Purpose | Path |
|---|---|
| Inference agent | `team_code/agent_simlingo.py` |
| Base model | `simlingo_base_training/models/driving.py` |
| Full model | `simlingo_training/models/driving.py` |
| LLaVA-Next encoder | `simlingo_base_training/models/encoder/llavanext.py` |
| InternVL2 encoder | `simlingo_training/models/encoder/vlm.py` |
| Base LLM (Llama) | `simlingo_base_training/models/language_model/llama.py` |
| Full LLM (InternVL2+LoRA) | `simlingo_training/models/language_model/llm.py` |
| PID controllers | `team_code/lateral_controller.py`, `team_code/longitudinal_controller.py` |
| Pretrained models | `pretrained/InternVL2-1B/` |
| Eval results | `eval_results/` |

## Dataset Generation

Language labels and dreaming data can be regenerated:
```bash
# VQA labels
python dataset_generation/language_labels/drivelm/carla_vqa_generator_main.py

# Commentary labels
python dataset_generation/language_labels/commentary/carla_commentary_generator_main.py

# Action dreaming data
python dataset_generation/dreamer_data/dreamer_generator.py
```

Route files are in `data/simlingo/`. Bucket assignments are computed via `dataset_generation/data_buckets/carla_get_buckets.py`.

## Core Dependencies

- PyTorch 2.2.0, PyTorch Lightning 2.4.0
- Transformers 4.46.3, PEFT 0.13.2 (LoRA), DeepSpeed 0.16.2
- Flash-Attention 2.7.0.post2
- CARLA 0.9.15 simulator
- Wandb 0.16.3 for experiment tracking
