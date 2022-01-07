from collections import defaultdict
from typing import Any, Callable, Hashable, Iterable, Literal, TypeVar, TypedDict

import openvr

from vr_to_joystick.mappings.nodes.value_generator import ValueGenerator

DeviceClass = Literal['controller', 'generic_tracker', 'hmd']

DEVICE_CLASS_NAME_TO_SUPPORTED_OPENVR_CONSTANTS: dict[DeviceClass, int] = {
    'controller': openvr.TrackedDeviceClass_Controller,
    'generic_tracker': openvr.TrackedDeviceClass_GenericTracker,
    'hmd': openvr.TrackedDeviceClass_HMD
}

ControllerRole = Literal['left_hand', 'right_hand', 'no_role']

CONTROLLER_ROLE_NAME_TO_SUPPORTED_OPENVR_CONSTANTS: dict[ControllerRole, int] = {
    'left_hand': openvr.TrackedControllerRole_LeftHand,
    'right_hand': openvr.TrackedControllerRole_RightHand,
    'no_role': openvr.TrackedControllerRole_Invalid,  # use 'no role' for HMD
}


class ControllerButtonStatePackage(TypedDict):
    touched: dict[int, bool]
    pressed: dict[int, bool]


class ControllerStatePackage(TypedDict):
    pose: openvr.HmdMatrix34_t
    velocity: openvr.HmdVector3_t
    angular_velocity: openvr.HmdVector3_t
    controller_state: openvr.VRControllerState_t
    button_state: ControllerButtonStatePackage


class VrSystemStatePackage(TypedDict):
    poses: dict[int, Iterable[openvr.TrackedDevicePose_t]]
    controller_state: dict[int, openvr.VRControllerState_t]
    button_state: dict[int, ControllerButtonStatePackage]


class VrSystemState(ValueGenerator[VrSystemStatePackage]):
    def __init__(self, vr_system: openvr.IVRSystem):
        super().__init__()
        self.vr_system = vr_system
        self.buttons_pressed: dict[int, dict[int, bool]] = defaultdict(lambda: defaultdict(bool))
        self.buttons_touched: dict[int, dict[int, bool]] = defaultdict(lambda: defaultdict(bool))

        # index 1: pose class (i.e. HMD vs Controller)
        # index 2: object role (e.g. left vs right hand. if N/A, role is always 0)
        self.device_indexes: dict[int, dict[int, int]] = defaultdict(dict)
        self.load_devices_by_index()

    def load_devices_by_index(self) -> None:
        self.device_indexes.clear()

        for i in range(openvr.k_unMaxTrackedDeviceCount):
            self.device_indexes[self.vr_system.getTrackedDeviceClass(
                i)][self.vr_system.getControllerRoleForTrackedDeviceIndex(i)] = i

    def device_id_for_type(self, device_class: DeviceClass, controller_role: ControllerRole = 'no_role') -> int:
        device_class_constant = DEVICE_CLASS_NAME_TO_SUPPORTED_OPENVR_CONSTANTS[device_class]
        controller_role_constant = CONTROLLER_ROLE_NAME_TO_SUPPORTED_OPENVR_CONSTANTS[controller_role]
        try:
            return self.device_indexes[device_class_constant][controller_role_constant]
        except KeyError:
            raise IndexError(f"No controller found for specified class '{device_class}' and role '{controller_role}'")

    def _poll_button_events(self) -> None:
        event = openvr.VREvent_t()
        while self.vr_system.pollNextEvent(event):
            if event.eventType == openvr.VREvent_ButtonTouch:
                print(f"Touch: {event.trackedDeviceIndex}, {event.data.controller.button}")
                self.buttons_touched[event.trackedDeviceIndex][event.data.controller.button] = True
            elif event.eventType == openvr.VREvent_ButtonUntouch:
                self.buttons_touched[event.trackedDeviceIndex][event.data.controller.button] = False
            elif event.eventType == openvr.VREvent_ButtonPress:
                print(f"Press: {event.trackedDeviceIndex}, {event.data.controller.button}")
                self.buttons_pressed[event.trackedDeviceIndex][event.data.controller.button] = True
            elif event.eventType == openvr.VREvent_ButtonUnpress:
                self.buttons_pressed[event.trackedDeviceIndex][event.data.controller.button] = False

    def _button_state_package(self) -> dict[int, ControllerButtonStatePackage]:
        controller_ids = set(self.buttons_pressed.keys()) | set(self.buttons_touched.keys())
        result: dict[int, ControllerButtonStatePackage] = defaultdict(
            lambda: ControllerButtonStatePackage(touched=defaultdict(bool), pressed=defaultdict(bool)))
        for controller_id in controller_ids:
            result[controller_id] = ControllerButtonStatePackage(
                touched=self.buttons_touched[controller_id],
                pressed=self.buttons_pressed[controller_id]
            )

        return result

    def _fetch_poses(self) -> dict[int, Iterable[openvr.TrackedDevicePose_t]]:
        # C-style array declaration: one device pose object per device being tracked
        # let it be known that i hate this
        poses_t = openvr.TrackedDevicePose_t * openvr.k_unMaxTrackedDeviceCount
        poses = poses_t()
        self.vr_system.getDeviceToAbsoluteTrackingPose(openvr.TrackingUniverseSeated, 0, poses)

        return poses  # type: ignore

    def _get_controller_states(self) -> dict[int, openvr.VRControllerState_t]:
        return {
            i: self.vr_system.getControllerState(i)[1]
            for i in range(openvr.k_unMaxTrackedDeviceCount)
        }

    def generate_output(self, _: Any) -> VrSystemStatePackage:
        self._poll_button_events()

        return VrSystemStatePackage(
            poses=self._fetch_poses(),
            button_state=self._button_state_package(),
            controller_state=self._get_controller_states(),
        )


O = TypeVar('O', bound=Hashable)


class VrSystemStateConsumer(ValueGenerator[O]):
    requirements = {'base_state'}

    def __init__(self, vr_system: VrSystemState):
        super().__init__(dependencies={'base_state': vr_system})


ControllerStateGenerator = VrSystemStateConsumer[ControllerStatePackage]


def ControllerState(controller_id: int) -> type[ControllerStateGenerator]:
    class _ConfiguredControllerState(ControllerStateGenerator):
        @classmethod
        def _parameterized_on(cls) -> list[Hashable]:
            return [controller_id]

        def generate_output(self, inputs: dict[str, Any]) -> ControllerStatePackage:
            return {
                'pose': inputs['base_state']['poses'][controller_id].mDeviceToAbsoluteTracking,
                'velocity': inputs['base_state']['poses'][controller_id].vVelocity,
                'angular_velocity': inputs['base_state']['poses'][controller_id].vAngularVelocity,
                'button_state': inputs['base_state']['button_state'][controller_id],
                'controller_state': inputs['base_state']['controller_state'][controller_id],
            }

    return _ConfiguredControllerState


class ControllerStateConsumer(ValueGenerator[O]):
    requirements = {'base_state'}

    def __init__(self, controller_state: ValueGenerator[ControllerStatePackage]):
        super().__init__(dependencies={'base_state': controller_state})

    def generate_output(self, inputs: dict[str, ControllerStatePackage]) -> O:
        return super().generate_output(inputs)


def ControllerStateByType(device_class: DeviceClass,
                          role: ControllerRole = 'no_role') -> Callable[[VrSystemState], ControllerStateGenerator]:
    def _GetControllerState(vr_system: VrSystemState) -> ControllerStateGenerator:
        return ControllerState(vr_system.device_id_for_type(device_class, role))(vr_system)

    return _GetControllerState
