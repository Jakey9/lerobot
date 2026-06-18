# Unitree G1 Humanoid Robot — LeRobot Integration

This guide covers using the Unitree G1 humanoid robot with LeRobot: from MuJoCo simulation (no hardware required) through data collection, training, and real-robot deployment.

## Overview

The G1 integration provides:
- **29-DOF joint control** (legs, waist, arms, wrists)
- **Built-in MuJoCo simulation** (default mode, no hardware needed)
- **ZMQ-based remote communication** for real hardware
- **IMU observations** (quaternion, gyroscope, accelerometer, RPY)
- **Camera support** via ZMQ streaming

### Joint Layout (29 DOF)

| Group | Joints | Indices |
|-------|--------|---------|
| Left leg | hip pitch/roll/yaw, knee, ankle pitch/roll | 0–5 |
| Right leg | hip pitch/roll/yaw, knee, ankle pitch/roll | 6–11 |
| Waist | yaw, roll, pitch | 12–14 |
| Left arm | shoulder pitch/roll/yaw, elbow | 15–18 |
| Left wrist | roll, pitch, yaw | 19–21 |
| Right arm | shoulder pitch/roll/yaw, elbow | 22–25 |
| Right wrist | roll, pitch, yaw | 26–28 |

---

## 1. Installation

### 1.1 Base LeRobot Setup

```bash
conda create -y -n lerobot python=3.10
conda activate lerobot
conda install ffmpeg -c conda-forge

cd /path/to/lerobot
pip install -e .
```

### 1.2 Unitree G1 Dependencies

```bash
# Unitree SDK2 Python (required for both sim and real)
pip install unitree_sdk2py

# MuJoCo (for simulation)
pip install mujoco

# ZMQ (for real hardware communication)
pip install pyzmq
```

---

## 2. Simulation (No Hardware Required)

The G1 driver has `is_simulation=True` by default. When enabled, it automatically downloads and runs a MuJoCo simulation environment from `lerobot/unitree-g1-mujoco` on Hugging Face Hub.

### 2.1 How Simulation Works

```
┌─────────────────────────────────────────────┐
│  Your Machine (single process)              │
│                                             │
│  UnitreeG1 Robot Driver                     │
│       │                                     │
│       ├── DDS channels over loopback (lo)   │
│       │                                     │
│       └── MuJoCo Sim (lerobot/unitree-g1-mujoco)
│            └── Steps physics at 250 Hz      │
└─────────────────────────────────────────────┘
```

### 2.2 Test Connection (Simulation)

```python
from lerobot.robots.unitree_g1 import UnitreeG1, UnitreeG1Config

config = UnitreeG1Config(is_simulation=True)
robot = UnitreeG1(config)
robot.connect()

# Read observation
obs = robot.get_observation()
print(f"Left hip pitch: {obs['kLeftHipPitch.q']:.4f} rad")

# Send action (hold current position)
action = {f"{k}.q": obs[f"{k}.q"] for k in [
    "kLeftHipPitch", "kLeftHipRoll", "kLeftHipYaw",
    "kLeftKnee", "kLeftAnklePitch", "kLeftAnkleRoll",
    # ... all 29 joints
]}
robot.send_action(action)

robot.disconnect()
```

### 2.3 Reset to Default Pose

```python
robot.reset()  # Interpolates all joints to default_positions over 3 seconds
```

---

## 3. Data Collection

### 3.1 Record Episodes (Simulation)

```bash
lerobot-record \
    --robot.type=unitree_g1 \
    --robot.is_simulation=true \
    --dataset.repo_id=my_user/g1_sim_data \
    --dataset.single_task="wave left hand" \
    --dataset.fps=50
```

### 3.2 Replay Recorded Episodes

```bash
lerobot-replay \
    --robot.type=unitree_g1 \
    --robot.is_simulation=true \
    --dataset.repo_id=my_user/g1_sim_data \
    --episode=0
```

### 3.3 Using Existing Unitree Datasets

Unitree provides pre-recorded datasets on Hugging Face (e.g. `unitreerobotics/G1_Dex3_ToastedBread_Dataset`). You can load and visualize them:

```bash
lerobot-dataset-viz \
    --repo-id unitreerobotics/G1_Dex3_ToastedBread_Dataset \
    --episode-index 0
```

---

## 4. Training

### 4.1 Train ACT Policy

```bash
python -m lerobot.scripts.lerobot_train \
    --dataset.repo_id=my_user/g1_sim_data \
    --policy.type=act \
    --policy.device=cuda \
    --output_dir=outputs/train/g1_act \
    --job_name=g1_act \
    --steps=500000
```

### 4.2 Train Diffusion Policy

```bash
python -m lerobot.scripts.lerobot_train \
    --dataset.repo_id=my_user/g1_sim_data \
    --policy.type=diffusion \
    --policy.device=cuda \
    --output_dir=outputs/train/g1_diffusion \
    --job_name=g1_diffusion \
    --steps=500000
```

### 4.3 Resume Training

```bash
python -m lerobot.scripts.lerobot_train \
    --dataset.repo_id=my_user/g1_sim_data \
    --policy.type=act \
    --policy.device=cuda \
    --output_dir=outputs/train/g1_act \
    --job_name=g1_act \
    --steps=800000 \
    --resume=true \
    --config_path=outputs/train/g1_act/checkpoints/last/pretrained_model/train_config.json
```

---

## 5. Evaluation in Simulation

### 5.1 Replay Policy in Sim

After training, you can evaluate the policy by replaying it through the robot in simulation:

```bash
lerobot-replay \
    --robot.type=unitree_g1 \
    --robot.is_simulation=true \
    --dataset.repo_id=my_user/g1_sim_data \
    --episode=0
```

### 5.2 Policy Inference Loop (Custom)

For more control over evaluation, use the robot driver directly:

```python
import torch
from lerobot.robots.unitree_g1 import UnitreeG1, UnitreeG1Config
from lerobot.policies.factory import make_policy
from lerobot.configs.policies import PreTrainedConfig
from lerobot.datasets.lerobot_dataset import LeRobotDatasetMetadata

# Load policy
policy_path = "outputs/train/g1_act/checkpoints/last/pretrained_model"
policy_cfg = PreTrainedConfig.from_pretrained(policy_path)
dataset_meta = LeRobotDatasetMetadata(repo_id="my_user/g1_sim_data")
policy = make_policy(cfg=policy_cfg, ds_meta=dataset_meta)

# Connect robot in simulation
config = UnitreeG1Config(is_simulation=True)
robot = UnitreeG1(config)
robot.connect()
robot.reset()

# Run inference loop
for step in range(1000):
    obs = robot.get_observation()
    # ... preprocess obs, run policy, postprocess action ...
    # robot.send_action(action)

robot.disconnect()
```

---

## 6. Real Hardware Deployment

### 6.1 Architecture

For real-robot deployment, a ZMQ bridge runs on the robot to forward DDS messages:

```
┌──────────────────────┐         ZMQ          ┌──────────────────────┐
│  Your Workstation    │◄───────────────────►  │  Unitree G1 Robot    │
│                      │   TCP ports 6000/6001 │                      │
│  UnitreeG1 driver    │                       │  run_g1_server.py    │
│  (is_simulation=False)                       │  (DDS ↔ ZMQ bridge)  │
└──────────────────────┘                       └──────────────────────┘
```

### 6.2 On the Robot: Start the DDS Bridge

SSH into the G1 and run:

```bash
python -m lerobot.robots.unitree_g1.run_g1_server
```

This bridges:
- Robot state (LowState) from DDS → ZMQ (port 6001, published to your workstation)
- Robot commands (LowCmd) from ZMQ (port 6000) → DDS (sent to robot motors)

### 6.3 On Your Workstation: Connect

```python
from lerobot.robots.unitree_g1 import UnitreeG1, UnitreeG1Config

config = UnitreeG1Config(
    is_simulation=False,
    robot_ip="192.168.123.164",  # G1's IP address
)
robot = UnitreeG1(config)
robot.connect()
```

### 6.4 Deploy a Trained Policy

```bash
# Record with a real robot (teleop required)
lerobot-record \
    --robot.type=unitree_g1 \
    --robot.is_simulation=false \
    --robot.robot_ip=192.168.123.164 \
    --dataset.repo_id=my_user/g1_real_data \
    --dataset.single_task="pick up cup" \
    --dataset.fps=50

# Replay a trained policy on real hardware
lerobot-replay \
    --robot.type=unitree_g1 \
    --robot.is_simulation=false \
    --robot.robot_ip=192.168.123.164 \
    --dataset.repo_id=my_user/g1_real_data \
    --episode=0
```

---

## 7. Configuration Reference

```python
@dataclass
class UnitreeG1Config(RobotConfig):
    # PD gains (per joint, grouped by body part)
    kp: list[float]  # Position gains [150,150,...,80,80,...,40,40,...]
    kd: list[float]  # Damping gains [2,2,...,3,3,...,1.5,1.5,...]

    # Default joint positions (29 floats, in radians)
    default_positions: list[float] = [0.0] * 29

    # Control loop frequency
    control_dt: float = 1.0 / 250.0  # 250 Hz

    # Simulation mode (True = MuJoCo, False = real robot)
    is_simulation: bool = True

    # Robot IP (only used when is_simulation=False)
    robot_ip: str = "192.168.123.164"

    # Cameras (ZMQ-based remote cameras)
    cameras: dict[str, CameraConfig] = {}
```

### PD Gain Groups

| Body Part | Kp | Kd |
|-----------|----|----|
| Left/Right leg (6 joints each) | [150, 150, 150, 300, 40, 40] | [2, 2, 2, 4, 2, 2] |
| Waist (3 joints) | [250, 250, 250] | [5, 5, 5] |
| Left/Right arm (4 joints each) | [80, 80, 80, 80] | [3, 3, 3, 3] |
| Left/Right wrist (3 joints each) | [40, 40, 40] | [1.5, 1.5, 1.5] |

---

## 8. File Structure

```
src/lerobot/robots/unitree_g1/
├── __init__.py              # Exports UnitreeG1, UnitreeG1Config
├── config_unitree_g1.py     # Configuration dataclass with PD gains
├── unitree_g1.py            # Main robot driver (sim + real)
├── g1_utils.py              # Joint index enums (G1_29_JointIndex)
├── unitree_sdk2_socket.py   # ZMQ-based DDS replacement for remote control
├── run_g1_server.py         # DDS↔ZMQ bridge (runs on the physical robot)
└── README.md                # This file
```

---

## 9. Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: unitree_sdk2py` | `pip install unitree_sdk2py` |
| `ModuleNotFoundError: mujoco` | `pip install mujoco` |
| Simulation hangs on connect | Ensure no other process is using DDS on loopback (`lo` interface) |
| Real robot not responding | Verify `run_g1_server.py` is running on the robot and IP is correct |
| ZMQ connection refused | Check firewall allows TCP ports 6000 and 6001 |
| Robot jerks on startup | Tune `kp`/`kd` gains or increase interpolation time in `reset()` |

---

## 10. References

- [Unitree G1 Product Page](https://www.unitree.com/g1/)
- [unitree_sdk2_python](https://github.com/unitreerobotics/unitree_sdk2_python)
- [unitreerobotics/unitree_lerobot](https://github.com/unitreerobotics/unitree_lerobot) — Unitree's official data conversion & eval toolkit
- [MuJoCo Simulation (HF Hub)](https://huggingface.co/lerobot/unitree-g1-mujoco)
- [LeRobot Documentation](https://huggingface.co/docs/lerobot/index)
