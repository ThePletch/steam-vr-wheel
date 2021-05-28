from steam_vr_wheel.mappings.nodes.button import Button, DirectButton
from steam_vr_wheel.mappings.nodes.button_helpers import AxisThresholdButton
import math

from steam_vr_wheel.mappings.nodes.value_generator import ValueGenerator
from steam_vr_wheel.mappings.nodes.axis import Axis, ControllerAxis, RollAxis, PitchAxis, XAxis, YAxis, YawAxis, ZAxis
from steam_vr_wheel.mappings.nodes.axis_helpers import ScaleAxis, AxisShifter
from steam_vr_wheel.mappings.nodes.vr_system_state import ControllerState, ControllerStateByType, ControllerStateGenerator, VrSystemState

from steam_vr_wheel.pyvjoy.vjoydevice import HID_USAGE_X, HID_USAGE_Y, HID_USAGE_Z, HID_USAGE_RX, HID_USAGE_RY, HID_USAGE_RZ, HID_USAGE_SL0
from steam_vr_wheel.controller_mapping import ControllerMapping
import openvr

ATAN_AXIS_SCALAR = 1 / (2 * math.pi)
TOUCHPAD_EDGE_BUTTON_THRESHOLD = 0.8
THUMBSTICK_EDGE_BUTTON_THRESHOLD = 0.8

STANDARD_BUTTONS = [
    openvr.k_EButton_SteamVR_Trigger,
    openvr.k_EButton_Grip,
    openvr.k_EButton_ApplicationMenu,
    openvr.k_EButton_SteamVR_Touchpad,
]

def standard_steamvr_controller_axis_profile(controller_state: ControllerStateGenerator) -> dict[int, Axis]:
    AtanAxisSquash = ScaleAxis(ATAN_AXIS_SCALAR, 0.0)
    return {
        HID_USAGE_X: XAxis(controller_state),
        HID_USAGE_Y: ScaleAxis(1, 1.5)(YAxis(controller_state)),
        HID_USAGE_Z: ScaleAxis(-1, -0.5)(ZAxis(controller_state)),
        HID_USAGE_RX: AtanAxisSquash(RollAxis(controller_state)),
        HID_USAGE_RY: ScaleAxis(1 / math.pi, 0.0)(YawAxis(controller_state)),
        HID_USAGE_RZ: AtanAxisSquash(AxisShifter(-1 * math.pi, math.pi, -math.pi / 2)(PitchAxis(controller_state))),
        HID_USAGE_SL0: ControllerAxis(1, 'x')(controller_state)  # trigger throttle
    }

def standard_steamvr_controller_button_profile(controller_state: ControllerStateGenerator) -> dict[int, Button]:
    basic_buttons = []
    for openvr_button_id in STANDARD_BUTTONS:
        basic_buttons.append(DirectButton(openvr_button_id, 'touch')(controller_state))
        basic_buttons.append(DirectButton(openvr_button_id, 'press')(controller_state))

    axial_buttons = [
        AxisThresholdButton(TOUCHPAD_EDGE_BUTTON_THRESHOLD, '>')(ControllerAxis(0, 'y')(controller_state)), # touchpad top
        AxisThresholdButton(TOUCHPAD_EDGE_BUTTON_THRESHOLD, '>')(ControllerAxis(0, 'x')(controller_state)), # touchpad right
        AxisThresholdButton(-1 * TOUCHPAD_EDGE_BUTTON_THRESHOLD, '<')(ControllerAxis(0, 'y')(controller_state)), # touchpad bottom
        AxisThresholdButton(-1 * TOUCHPAD_EDGE_BUTTON_THRESHOLD, '<')(ControllerAxis(0, 'x')(controller_state)), # touchpad left
        AxisThresholdButton(THUMBSTICK_EDGE_BUTTON_THRESHOLD, '>')(ControllerAxis(2, 'y')(controller_state)), # thumbstick top
        AxisThresholdButton(THUMBSTICK_EDGE_BUTTON_THRESHOLD, '>')(ControllerAxis(2, 'x')(controller_state)), # thumbstick right
        AxisThresholdButton(-1 * THUMBSTICK_EDGE_BUTTON_THRESHOLD, '<')(ControllerAxis(2, 'y')(controller_state)), # thumbstick bottom
        AxisThresholdButton(-1 * THUMBSTICK_EDGE_BUTTON_THRESHOLD, '<')(ControllerAxis(2, 'x')(controller_state)), # thumbstick left
    ]


    return {
        i + 1: button
        for i, button in enumerate([*basic_buttons, *axial_buttons])
    }

class StandardController(ControllerMapping):
    required_devices = [
        ('controller', 'right_hand')
    ]

    def generate_axis_mapping(self, root_node: VrSystemState) -> dict[int, Axis]:
        return standard_steamvr_controller_axis_profile(ControllerStateByType('controller', 'right_hand')(root_node))
        

    def generate_button_mapping(self, root_node: VrSystemState) -> dict[int, Button]:
        return standard_steamvr_controller_button_profile(ControllerStateByType('controller', 'right_hand')(root_node))

        
