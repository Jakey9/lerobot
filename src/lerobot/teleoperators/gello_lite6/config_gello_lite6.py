from dataclasses import dataclass
from typing import Tuple

from lerobot.teleoperators import TeleoperatorConfig


@TeleoperatorConfig.register_subclass("gello_lite6")
@dataclass
class GelloLite6Config(TeleoperatorConfig):
    port: str = "/dev/ttyUSB0"
    baudrate: int = 115200
    joint_ids: Tuple[int, ...] = (0, 1, 2, 3, 4, 5)
    joint_signs: Tuple[int, ...] = (1, 1, 1, 1, 1, 1)
    start_joints: Tuple[float, ...] = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    gripper_id: int = 6  # set to -1 if no gripper
