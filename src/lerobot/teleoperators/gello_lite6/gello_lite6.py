import logging
import time

import numpy as np

from lerobot.teleoperators import Teleoperator
from lerobot.utils.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError

from .config_gello_lite6 import GelloLite6Config

logger = logging.getLogger(__name__)


class GelloLite6(Teleoperator):
    """GELLO teleoperator for UFFactory Lite6 using Zhonglin serial bus servos."""

    config_class = GelloLite6Config
    name = "gello_lite6"

    def __init__(self, config: GelloLite6Config):
        super().__init__(config)
        self.config = config
        self._is_connected = False
        self._is_calibrated = True

        from gello.zhonglin.driver import ZhonglinDriver
        from gello.agents.gello_agent import ZhonglinRobotConfig

        joint_ids = list(self.config.joint_ids)
        if self.config.gripper_id >= 0:
            joint_ids.append(self.config.gripper_id)

        driver = ZhonglinDriver(
            joint_ids, port=self.config.port, baudrate=self.config.baudrate
        )
        for _ in range(10):
            driver.get_joints()
        curr_joints = driver.get_joints()
        driver.close()

        joint_offsets = []
        for i in range(len(self.config.start_joints)):
            offset = (
                curr_joints[i]
                - self.config.start_joints[i] / self.config.joint_signs[i]
            )
            joint_offsets.append(offset)

        if self.config.gripper_id >= 0:
            gripper_config = (
                self.config.gripper_id,
                np.rad2deg(curr_joints[-1]) - 0.2,
                np.rad2deg(curr_joints[-1]) - 42,
            )
        else:
            gripper_config = None

        self._zhonglin_config = ZhonglinRobotConfig(
            joint_ids=self.config.joint_ids,
            joint_signs=self.config.joint_signs,
            joint_offsets=joint_offsets,
            gripper_config=gripper_config,
            baudrate=self.config.baudrate,
        )
        print(self._zhonglin_config)
        self.dof = len(self.config.start_joints)

    @property
    def action_features(self) -> dict:
        return {f"J{i+1}.pos": float for i in range(self.dof)} | {"gripper.pos": float}

    @property
    def feedback_features(self) -> dict:
        return {f"J{i+1}.pos": float for i in range(self.dof)} | {"gripper.pos": float}

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def connect(self, calibrate: bool = True) -> None:
        if self._is_connected:
            raise DeviceAlreadyConnectedError(f"{self} already connected")

        from gello.agents.gello_agent import GelloAgent

        self.gello_agent = GelloAgent(
            port=self.config.port, zhonglin_config=self._zhonglin_config
        )

        if not self._is_calibrated and calibrate:
            logger.info("No calibration found, running calibration")
            self.calibrate()

        self.configure()
        self._is_connected = True
        logger.info(f"{self} connected.")

    @property
    def is_calibrated(self) -> bool:
        return self._is_calibrated

    def calibrate(self) -> None:
        pass

    def configure(self) -> None:
        pass

    def get_action(self) -> dict[str, float]:
        start = time.perf_counter()
        fake_obs = {"joint_state": np.zeros(self.dof + 1)}
        action_array = self.gello_agent.act(fake_obs)
        dt_ms = (time.perf_counter() - start) * 1e3
        logger.debug(f"{self} read action: {dt_ms:.1f}ms")

        action = {}
        for i in range(self.dof):
            action[f"J{i+1}.pos"] = action_array[i]
        action["gripper.pos"] = action_array[self.dof]
        return action

    def send_feedback(self, feedback: dict[str, float]) -> None:
        raise NotImplementedError

    def disconnect(self) -> None:
        if not self._is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")
        self._is_connected = False
        logger.info(f"{self} disconnected.")
