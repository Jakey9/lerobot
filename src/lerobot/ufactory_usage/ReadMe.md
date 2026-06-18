# UFACTORY Data Collection Guide(Imitation Learning)

## ⚠️ Important Notice
Using gello to collect dataset:
- Once data collection starts, **the relative position between the robot arm and the camera (D435/D435i) must not be changed**.  
- When making the inference, the position of the camera and the collection must be the same. Otherwise, the collected data will become invalid.  
- In case of change, the entire process must be re-performed:

```
Collect Dataset → Train the model → Perform Inference and Evaluation
```

Using pika to collect dataset:
- There are no specific requirements for the relative positions of the two pika stations and the robotic arm. However, **the pika needs to be recalibrated after the station moves**.
- The positions of the pika stations during the collection and inference processes do not have to be the same.

## 1. Hardware Requirements

### Reference Hardware Setup
- **Robot Arm**: [UFACTORY xArm7](https://www.ufactory.cc/xarm-collaborative-robot/)
- **End Effector**: [UFACTORY xArm Gripper](https://www.ufactory.cc/product-page/ufactory-xarm-gripper/)
- **Camera**:  
  - [Intel RealSense D435](https://www.realsenseai.com/products/stereo-depth-camera-d435/)  
  - [Intel RealSense D435i](https://www.realsenseai.com/products/depth-camera-d435i/)
- **Camera Mount**: Provided by UFACTORY (purchase or 3D print)
  - Purchase: [UFACTORY Camera Stand](https://www.ufactory.cc/product-page/ufactory-xarm-camera-stand/)
  - 3D Model: [Realsense_Camera_Stand.STEP](https://www.ufactory.cc/wp-content/uploads/2024/05/CameraStand_1300.zip)
- **Teleoperation Device**: gello, [pika](https://global.agilex.ai/products/pika)

---

## 2. Software Environment Setup

### 2.1 Using gello

#### Install librealsense

Reference: [librealsense Linux Installation Guide](https://github.com/realsenseai/librealsense/blob/master/doc/distribution_linux.md)

##### Register Public Key
```bash
sudo mkdir -p /etc/apt/keyrings
curl -sSf https://librealsense.realsenseai.com/Debian/librealsense.pgp | sudo tee /etc/apt/keyrings/librealsense.pgp > /dev/null
```

##### Install APT HTTPS Support
```bash
sudo apt-get install apt-transport-https
```

##### Add the server to the list of repository
```bash
echo "deb [signed-by=/etc/apt/keyrings/librealsenseai.gpg] https://librealsense.realsenseai.com/Debian/apt-repo `lsb_release -cs` main" | \
sudo tee /etc/apt/sources.list.d/librealsense.list
sudo apt-get update
```

##### Install librealsense
```bash
sudo apt-get install librealsense2-dkms
sudo apt-get install librealsense2-utils
```
### 2.2 Using pika
Please refer to [pika tracking device calibration](https://github.com/xArm-Developer/ufactory_teleop/tree/main/pika_teleop).  
First-time use of Pika Sense or when the base station position changes requires calibration.


## 3. Lerobot Environment Setup
### 3.1 Create Python Virtual Environment

#### Linux (Conda)
```bash
conda create -y -n lerobot python=3.10
conda activate lerobot
```

#### Install ffmpeg
```bash
conda install ffmpeg -c conda-forge
```


### 3.2 Install LeRobot and Dependencies

#### Install LeRobot
```bash
git clone https://github.com/xArm-Developer/lerobot.git
cd lerobot
pip install -e .
```

#### Install Additional Dependencies
```bash
cd src/lerobot/ufactory_usage
pip install -r requirements_extra.txt

cd src/gello
pip install -e third_party/DynamixelSDK/python
pip install numpy tyro
pip install -e .
pip install pyrealsense2  # 2.56.5.9235
pip install git+https://github.com/xArm-Developer/xArm-Python-SDK.git
```

## 4. Data Collection

### 4.1 Teleoperation Test

#### Using gello (xArm7)
1. Modify the configuration file (example: `xarm7_gello_record_config.yaml`)
   - **RobotConfig**
     - `robot_ip`: IP address of the robot
     - `robot_dof`: Degrees of freedom
     - `start_joints`: Initial joint positions
   - **TeleoperatorConfig**
     - `start_joints`: Initial joint positions
2. Move the gello joints to match the robot's initial pose;
3. Start the script:
```bash
python uf_robot_teleop_test.py --config config/xarm7_gello_record_config.yaml
```
4. Press **Enter** to begin teleoperation;
5. Press **ESC** to exit.


#### Using pika (xArm7)
1. Modify the configuration file (example: `xarm7_pika_record_config.yaml`)
   - **RobotConfig**
     - `robot_ip`: IP address of the robot
     - `robot_dof`: Degrees of freedom
     - `start_joints`: Initial joint positions
   - **TeleoperatorConfig**
     - `start_joints`: Initial joint positions
     - `gripper-port`: Pika gripper serial port
     - `index_or_path`: Pika gripper camera index
     - `port`: Pika sense serial port
2. Move the pika sense to the initial position;
3. Start the script:
```bash
python uf_robot_teleop_test.py --config config/xarm7_pika_record_config.yaml
```
1. Double click pika sense to start teleoperation;
2. Press **ESC** to exit.

### 4.2 Data Recording
**Users may define their own data collection strategies. LeRobot only enforces the dataset format.**

**Keyboard control** for data recording:  
- "`->`" Exit early: Finish current episode, save and enter reset process for next episode preparation;  
- "`<-`" rerecord_episode + Exit early: Terminate current recording, reset and then re-record this episode;  
- "`Esc`" stop_recording + Exit early: Exit recording process;
- "`Enter`" : Continue

#### Recording with gello(teleoperation)
```bash
# the default dataset is stored in lerobot_datas/record in the same directory as lerobot.
python uf_robot_record.py --config config/xarm7_gello_record_config.yaml
```

#### Recording with scripts(Randomly Generated Targets)
```bash
# the default dataset is stored in lerobot_datas/record in the same directory as lerobot.
python uf_robot_record.py --config config/xarm7_mock_record_config.yaml
```

#### Recording with pika(teleoperation)
```bash
# the default dataset is stored in lerobot_datas/record in the same directory as lerobot.
python uf_robot_record.py --config config/xarm7_pika_record_config.yaml
```

### 4.3 Resume Data Recording

#### Resume gello-based recording
```bash
# the default dataset is stored in lerobot_datas/record in the same directory as lerobot.
python uf_robot_record.py --config config/xarm7_gello_record_config.yaml --resume
```
#### Resume random target recording
```bash
# the default dataset is stored in lerobot_datas/record in the same directory as lerobot.
python uf_robot_record.py --config config/xarm7_mock_record_config.yaml --resume
```

#### Resume pika-based recording
```bash
# the default dataset is stored in lerobot_datas/record in the same directory as lerobot.
python uf_robot_record.py --config config/xarm7_pika_record_config.yaml --resume
```

## 5. Training

### 5.1 Initial Training(Use ACT)
```bash
# Note:
# repo_id must match the value used during data collection
# policy.type is set to 'act'
# steps = 800,000
# Model checkpoints are saved every 20,000 steps, and outputs the results to lerobot_datas/train in the same directory as lerobot.
python -m lerobot.scripts.lerobot_train \
  --dataset.root=../../../../lerobot_datas/record/ufactory/xarm7_record_datas \
  --dataset.repo_id=ufactory/xarm7_record_datas \
  --policy.type=act \
  --output_dir=../../../../lerobot_datas/train/xarm7_record_datas \
  --job_name=xarm7_record_datas \
  --policy.device=cuda \
  --policy.repo_id=ufactory/xarm7_record_datas \
  --steps=800000
```

### 5.2 Resume Training
```bash
python -m lerobot.scripts.lerobot_train \
  --dataset.root=../../../../lerobot_datas/record/ufactory/xarm7_record_datas \
  --dataset.repo_id=ufactory/xarm7_record_datas \
  --policy.type=act \
  --output_dir=../../../../lerobot_datas/train/xarm7_record_datas \
  --job_name=xarm7_record_datas \
  --policy.device=cuda \
  --policy.repo_id=ufactory/xarm7_record_datas \
  --steps=800000 \
  --batch_size=8 \
  --save_freq=20000 \
  --resume=true \
  --config_path=outputs/train/xarm7_record_datas/checkpoints/last/pretrained_model/train_config.json
```

## 6. Inference & Evaluation

### Run with a Specified Model
```bash
python uf_robot_eval.py \
  --config config/xarm7_gello_record_config.yaml \
  --policy.path=../../../../lerobot_datas/train/xarm7_record_datas/checkpoints/last/pretrained_model/
```

## 7. Lite6 + Gello (Zhonglin Servo) Guide

This section covers using a **UFACTORY Lite6** robot arm with a custom **GELLO** teleoperator built with **Zhonglin serial bus servos** (not Dynamixel).

### 7.1 Hardware Requirements

- **Robot Arm**: [UFACTORY Lite6](https://www.ufactory.cc/lite6-collaborative-robot/)
- **Teleoperator**: Custom GELLO with Zhonglin serial bus servos (6-DOF, optional gripper on servo ID 6)
- **Camera**: Intel RealSense D435/D435i/D455
- **Connection**: Zhonglin servos via USB-to-serial adapter (`/dev/ttyUSB0`)

### 7.2 Software Setup (Forked gello_software)

The default `requirements_extra.txt` installs the upstream gello_software, which only supports Dynamixel motors. For Zhonglin servos, install the **forked version** instead:

```bash
# Do NOT run: pip install -r requirements_extra.txt (it pulls the wrong gello repo)

# Install the forked gello_software with Zhonglin driver support
cd /path/to/your/gello_software
pip install -e .

# Install DynamixelSDK (still needed as a dependency)
pip install -e third_party/DynamixelSDK/python
```

Verify the install provides these modules:
- `gello.zhonglin.driver` (`ZhonglinDriver`)
- `gello.agents.gello_agent` (`GelloAgent`, `ZhonglinRobotConfig`)

### 7.3 Configuration

Edit `config/lite6_gello_record_config.yaml`:

```yaml
RobotConfig:
  _target_: lerobot.robots.ufactory_robot.UFRobotConfig
  id: "lite6"
  robot_ip: "192.168.1.85"       # Your lite6 IP
  robot_dof: 6
  control_space: "joint"
  gripper_control: False
  start_joints: [0, 0, 0, 0, 0, 0]
  cameras:
    overhead:
      _target_: lerobot.cameras.realsense.configuration_realsense.RealSenseCameraConfig
      serial_number_or_name: "Intel RealSense D455"
      fps: 30
      width: 640
      height: 480

TeleoperatorConfig:
  _target_: lerobot.teleoperators.gello_lite6.GelloLite6Config
  port: "/dev/ttyUSB0"           # Serial port for Zhonglin servos
  baudrate: 115200
  joint_ids: [0, 1, 2, 3, 4, 5]
  joint_signs: [1, 1, 1, 1, 1, 1]
  start_joints: [0, 0, 0, 0, 0, 0]  # Robot pose that gello matches at startup
  gripper_id: -1                 # Set to 6 when gripper servo is connected
```

### 7.4 Calibration

Offset calibration is **automatic** — computed each time the script starts. The procedure:

1. Command the Lite6 to its home position (all joints at 0 radians)
2. Physically move the GELLO so its joints mirror the robot's home pose
3. Ensure `start_joints` in the YAML matches the robot's current pose (e.g. `[0, 0, 0, 0, 0, 0]`)
4. Run the script — offsets are calculated as: `offset[i] = raw_servo[i] - start_joints[i] / joint_signs[i]`

To verify offsets before running the full pipeline:
```bash
cd /path/to/your/gello_software
python scripts/zhonglin_get_offset.py --port /dev/ttyUSB0 --start-joints 0 0 0 0 0 0
```

### 7.5 Teleoperation Test

```bash
python uf_robot_teleop_test.py --config config/lite6_gello_record_config.yaml
```

- Press **Enter** to begin teleoperation
- Press **ESC** to exit

### 7.6 Data Recording

```bash
python uf_robot_record.py --config config/lite6_gello_record_config.yaml
```

Keyboard controls during recording:
- `→` : Finish current episode, save, and reset for next episode
- `←` : Discard current episode, reset, and re-record
- `Esc` : Stop recording and exit
- `Enter` : Continue

### 7.7 Training (Lite6)

```bash
python -m lerobot.scripts.lerobot_train \
  --dataset.root=../../../../lerobot_datas/record/ufactory/lite6_record_datas \
  --dataset.repo_id=ufactory/lite6_record_datas \
  --policy.type=act \
  --output_dir=../../../../lerobot_datas/train/lite6_record_datas \
  --job_name=lite6_record_datas \
  --policy.device=cuda \
  --policy.repo_id=ufactory/lite6_record_datas \
  --steps=800000
```

### 7.8 Inference & Evaluation (Lite6)

```bash
python uf_robot_eval.py \
  --config config/lite6_gello_record_config.yaml \
  --policy.path=../../../../lerobot_datas/train/lite6_record_datas/checkpoints/last/pretrained_model/
```

---

## 8. Dataset Utilities

### Playback an Episode
Example: view episode index **17**
```bash
lerobot-dataset-viz \
  --root=../../../../lerobot_datas/record/ufactory/xarm7_record_datas \
  --repo-id ufactory/xarm7_record_datas \
  --display-compressed-images true \
  --episode-index 17
```

### Delete Episodes
Example: delete episodes **18** and **19**
```bash
lerobot-edit-dataset \
  --root=../../../../lerobot_datas/record/ufactory/xarm7_record_datas \
  --repo_id ufactory/xarm7_record_datas \
  --new_repo_id ../xarm7_record_datas_new \
  --operation.type delete_episodes \
  --operation.episode_indices "[18, 19]"
```

### Merge Datasets
```bash
lerobot-edit-dataset \
  --root=../../../../lerobot_datas/record \
  --repo_id ufactory/xarm7_record_datas_merge_1_2 \
  --operation.type merge \
  --operation.repo_ids "['ufactory/xarm7_record_datas_1', 'ufactory/xarm7_record_datas_2']"
```


## 9. Important Notes
Users are expected to thoroughly study the codebase and configuration parameters.  
The provided configurations are **not guaranteed to work for all scenarios** and must be adjusted based on actual hardware setups and task requirements.

In particular, for **diffusion policies**, the default parameters in LeRobot are primarily designed for simulation and **are not optimized for real-world robots**.


## 10. Dataset Examples (Reference Only)
[Test datasets](https://drive.google.com/drive/folders/1Ms25rd2YYGdh3tHPEsTTMU-m1fE7uNYY?usp=sharing) used during development (not reusable):
- **xarm7_act_20260119**: 60 successful single-attempt grasps recorded via gello
- **xarm7_act_20260127**: 80 samples (added 20 failure-and-retry cases)
- **xarm7_act_mock_20260126**: 60 one-shot grasps generated programmatically
- **xarm7_pika_datas_aa_merge_0208_0209_2pi**: 150 samples grasps recorded via pika

> These datasets are **for reference only**.  
> They cannot be reused because the robot–camera position differs between users.

* Train using xarm7_act_20260127 for 500,000 training steps.
  [![watch the video](assets/inference-gello.png)](https://www.youtube.com/watch?v=wTiWLiHciT8)
* Train xarm7_pika_datas_aa_merge_0208_0209_2pi for 400,000 training steps.
  [![watch the video](assets/inference-pika.png)](https://youtu.be/IiyvewZh5OY)
