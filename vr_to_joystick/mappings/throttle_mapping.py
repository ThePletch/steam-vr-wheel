import openvr
from pyvjoy.vjoydevice import HID_USAGE_X, HID_USAGE_Y, HID_USAGE_Z

from vr_to_joystick.controller_mapping import ControllerMapping
from vr_to_joystick.nodes.axis import ControllerAxis, ZAxis
from vr_to_joystick.nodes.axis_helpers import ScaleAxis, PushPullAxis
from vr_to_joystick.nodes.button import DirectButton
from vr_to_joystick.nodes.button_helpers import AxisThresholdButton, GestureButton
from vr_to_joystick.nodes.composite.axis import InvertedAxis
from vr_to_joystick.nodes.types import Axis, Button
from vr_to_joystick.nodes.vr_system_state import ControllerStateByType, VrSystemState


# CONFIG SETTINGS FOR MAPPING
TWIST_GESTURE_THRESHOLD = 0.8
TOUCHPAD_EDGE_BUTTON_THRESHOLD = 0.7
THUMBSTICK_EDGE_BUTTON_THRESHOLD = 0.8

"""
Mapping for VR space flight in Elite: Dangerous.
WORK IN PROGRESS
Intended features:
    Both controllers:
        Switch cockpit mode: Hold controllers close together and flick both controllers twice
    Left controller:
        SPACE FLIGHT:
            Toggle throttle/thruster mode: Press grip 3x
            THROTTLE MODE:
                Adjust throttle: Hold grip, rotate controller CW, then move forward/backward
                Lateral/vertical thrusters: Thumbstick
                Boost: While adjusting throttle, flick controller
                    * This works off velocity, not distance, so a firm flick is enough
            THRUSTER MODE:
                Apply thrust: Hold grip, rotate controller CW, then move controller in desired thrust direction.
                    * Thrust scales with distance moved
                    * Release grip to stop thrust
        Manage system power: Trackpad
        SENSORS:
            Hold controller below you (triggers buzz)
                Adjust zoom: Hold grip and twist CW/CCW (clockwise zooms in)
        COUNTERMEASURES:
            Hold controller off to left side (triggers buzz)
                Toggle silent running: Hold grip and twist CW or CCW
                Deploy heatsink: Hold grip and pull toward you
                Launch chaff: Hold grip and move controller down
                Activate shield cell: Hold grip and move controller up
        VISION:
            Hold controller above you (triggers buzz)
                Toggle nightvision: Hold grip and pull down
                Toggle headlights: Hold grip and twist CW
        WEAPONS:
            Secondary fire: Press trigger
        TARGETING:
            Select target in sights: Press thumbstick

    Right controller:
        SPACE FLIGHT:
            Rotate ship: Double-press and hold grip, then twist controller in desired rotation direction.
                * Rotation scales with distance moved
                * Release grip to stop rotation
            Toggle flight assist: Raise controller over head and flick
            Primary fire: Press trigger
        WEAPONS:
            Cycle fire groups: Press trackpad L or R
            Toggle hardpoint deployment: Press trackpad U
        SHIP MODE MANAGEMENT:
            Hold controller below you (triggers buzz)
                Cargo scoop: Hold grip, push controller down
                Landing gear: Hold grip, push controller up
        FRAME SHIFT:
            Hold controller off to right side (triggers buzz)
                Activate FSD: Flick controller
                Supercruise: Hold grip, twist CW (will trigger buzz), and flick controller
                Hyperspace: Hold grip, twist CCW (will trigger buzz), and flick controller
        INTERFACE:
            Move through interface: Thumbstick
            Select interface item: Press thumbstick
            Back: Press menu button
            Next/previous tab: Hold grip and move controller left/right
"""


class ThrottleMapping(ControllerMapping):
    required_devices = [
        ('controller', 'right_hand')
    ]

    def generate_axis_mapping(self, root_node: VrSystemState) -> dict[int, Axis]:
        controller_state = ControllerStateByType('controller', 'right_hand')(root_node)
        grip_button = DirectButton(openvr.k_EButton_Grip, 'press')(controller_state)
        thumb_x = ControllerAxis(2, 'x')(controller_state)
        thumb_y = ControllerAxis(2, 'y')(controller_state)

        return {
            HID_USAGE_X: ScaleAxis(0.5, 0)(thumb_x),
            HID_USAGE_Y: ScaleAxis(0.5, 0)(thumb_y),
            HID_USAGE_Z: InvertedAxis(PushPullAxis(grip_button, ZAxis(controller_state)))
        }

    def generate_button_mapping(self, root_node: VrSystemState) -> dict[int, Button]:
        controller_state = ControllerStateByType('controller', 'right_hand')(root_node)

        buttons = [
            DirectButton(openvr.k_EButton_SteamVR_Trigger, 'press')(controller_state),
            GestureButton(0.5, '>')(
                AxisThresholdButton(TOUCHPAD_EDGE_BUTTON_THRESHOLD, '>')(ControllerAxis(0, 'y')(controller_state)),
                InvertedAxis(ZAxis(controller_state))
            )
        ]

        return {
            i + 1: button
            for i, button in enumerate(buttons)
        }
