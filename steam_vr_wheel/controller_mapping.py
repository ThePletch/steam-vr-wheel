from abc import abstractmethod
import logging
import time
from steam_vr_wheel.mappings.nodes.axis import Axis
from steam_vr_wheel.mappings.nodes.button import Button
from steam_vr_wheel.mappings.nodes.value_generator import ValueConsumer
from steam_vr_wheel.mappings.nodes.vr_system_state import ControllerRole, DeviceClass, VrSystemState
from typing import Iterable, Iterator

import openvr
from pyvjoy.vjoydevice import VJoyDevice

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(level name)s] %(name)s - %(message)s")

SUPPORTED_BUTTON_EVENTS = [
    openvr.VREvent_ButtonTouch,
    openvr.VREvent_ButtonUntouch,
    openvr.VREvent_ButtonPress,
    openvr.VREvent_ButtonUnpress
]


def events(vr_system: openvr.IVRSystem) -> Iterator[openvr.VREvent_t]:
    event = openvr.VREvent_t()
    while vr_system.pollNextEvent(event):
        yield event


class ControllerMapping:
    AXIS_PRECISION = 0x8000
    DEVICE_WAIT_TIMEOUT = 120  # two minutes
    DEVICE_POLL_TIME = 5       # five seconds
    vr_system: openvr.IVRSystem
    vjoy_device_id: int

    root_node: VrSystemState
    vjoy_device: VJoyDevice
    axis_mapping: dict[int, Axis]
    button_mapping: dict[int, Button]

    # we can't use a dataclass for this, since dataclasses break for abstract methods
    def __init__(self, vr_system: openvr.IVRSystem, vjoy_device_id: int):
        self.vr_system = vr_system
        self.vjoy_device_id = vjoy_device_id

        logger.info("Binding to VR system...")
        self.root_node = VrSystemState(self.vr_system)
        logger.info(f"VR system bound. Claiming target VJoy device {self.vjoy_device_id}...")
        self.vjoy_device = VJoyDevice(self.vjoy_device_id)
        logger.info(f"Claimed. Polling for required controllers...")
        self.wait_for_required_devices()
        logger.info("All required controllers found.")
        self.axis_mapping = self.generate_axis_mapping(self.root_node)
        self.button_mapping = self.generate_button_mapping(self.root_node)
        self.event_triggers = self.generate_event_triggers(self.root_node)
        self.current_tick = -1

    @property
    def required_devices(self) -> Iterable[tuple[DeviceClass, ControllerRole]]:
        raise NotImplementedError("Controller mappings must enumerate the devices they expect to be present.")

    def wait_for_required_devices(self) -> None:
        time_waited = 0
        while time_waited < self.DEVICE_WAIT_TIMEOUT:
            if not (missing_controllers := self.controllers_missing()):
                return

            missing_list = ", ".join(".".join(controller) for controller in missing_controllers)
            logger.info(f"Waiting for controller(s): {missing_list}")
            logger.debug(f"Polling again in {self.DEVICE_POLL_TIME} seconds...")
            time.sleep(self.DEVICE_POLL_TIME)
            time_waited += self.DEVICE_POLL_TIME
            self.root_node.load_devices_by_index()

        raise TimeoutError(
            f"Waited longer than maximum wait time of {self.DEVICE_WAIT_TIMEOUT} for required controllers. Giving up.")

    def controllers_missing(self) -> list[tuple[DeviceClass, ControllerRole]]:
        missing_controllers: list[tuple[DeviceClass, ControllerRole]] = []
        for device_class, controller_role in self.required_devices:
            try:
                self.root_node.device_id_for_type(device_class, controller_role)
            except IndexError:
                missing_controllers.append((device_class, controller_role))

        return missing_controllers

    # a series of nodes stemming from the root node that generate a mapping to vjoy axes
    @abstractmethod
    def generate_axis_mapping(self, root_node: VrSystemState) -> dict[int, Axis]:
        pass

    @abstractmethod
    def generate_button_mapping(self, root_node: VrSystemState) -> dict[int, Button]:
        pass

    def generate_event_triggers(self, root_node: VrSystemState) -> list[ValueConsumer]:
        return []

    def tick(self) -> None:
        self.current_tick += 1
        self.root_node.update(self.current_tick)

        self.sync_axes()
        self.sync_buttons()

    def sync_axes(self) -> None:
        for axis_id, axis_node in self.axis_mapping.items():
            self.vjoy_device.set_axis(axis_id, int(axis_node.current_value * self.AXIS_PRECISION))

    def sync_buttons(self) -> None:
        for button_id, button_node in self.button_mapping.items():
            self.vjoy_device.set_button(button_id, button_node.current_value['active'])
