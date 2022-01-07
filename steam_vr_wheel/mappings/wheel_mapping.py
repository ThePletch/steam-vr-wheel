from steam_vr_wheel.mappings.nodes.event_triggers import HapticPulseTrigger
from steam_vr_wheel.mappings.nodes.value_generator import ValueConsumer
from typing import Iterable
import openvr
import math

from steam_vr_wheel.mappings.nodes.composite.axis import DifferenceAxis
from steam_vr_wheel.mappings.nodes.button_helpers import AxisThresholdButton, CircleGesture, GestureButton, MultiClickButton, SequentialGesture, ToggleButton
from steam_vr_wheel.mappings.nodes.composite.button import AndButton, NotButton, StickyPairButton
from steam_vr_wheel.mappings.nodes.axis import Axis, ControllerAxis, PitchAxis, RollAxis, XAxis, YAxis, ZAxis


from steam_vr_wheel.mappings.nodes.button import Button, DirectButton
from steam_vr_wheel.mappings.nodes.axis_helpers import DeadzoneAxis, GatedAxis, ScaleAxis
from steam_vr_wheel.mappings.nodes.vr_system_state import ControllerStateByType, ControllerStateGenerator, VrSystemState
from steam_vr_wheel.mappings.nodes.wheel import Wheel
from steam_vr_wheel.controller_mapping import ControllerMapping

from pyvjoy.vjoydevice import HID_USAGE_X, HID_USAGE_Y, HID_USAGE_Z, HID_USAGE_RX, HID_USAGE_RY, HID_USAGE_RZ, HID_USAGE_SL0, HID_USAGE_SL1

TWIST_GESTURE_THRESHOLD = 0.8
TOUCHPAD_EDGE_BUTTON_THRESHOLD = 0.7
THUMBSTICK_EDGE_BUTTON_THRESHOLD = 0.8
TRANSLATIONAL_GESTURE_THRESHOLD = 0.05


class WheelMapping(ControllerMapping):
    required_devices = [
        ('hmd', 'no_role'),
        ('controller', 'left_hand'),
        ('controller', 'right_hand')
    ]

    def generate_axis_mapping(self, root_node: VrSystemState) -> dict[int, Axis]:
        hmd_state = ControllerStateByType('hmd')(root_node)
        left_controller_state = ControllerStateByType('controller', 'left_hand')(root_node)
        right_controller_state = ControllerStateByType('controller', 'right_hand')(root_node)

        grip_button = DirectButton(openvr.k_EButton_Grip, 'press')

        HALF_CIRCLE_ROTATION_SCALAR = 2 / math.pi

        return {
            # left thumbstick
            HID_USAGE_X: ScaleAxis(0.5, 0)(ControllerAxis(2, 'x')(left_controller_state)),
            HID_USAGE_Y: ScaleAxis(0.5, 0)(ControllerAxis(2, 'y')(left_controller_state)),
            # left/right roll axis of HMD
            HID_USAGE_Z: ScaleAxis(HALF_CIRCLE_ROTATION_SCALAR, 0)(DeadzoneAxis(math.pi / 10)(RollAxis(hmd_state))),
            # pitch axis of HMD
            HID_USAGE_RX: ScaleAxis(HALF_CIRCLE_ROTATION_SCALAR, 0)(DeadzoneAxis(math.pi / 10)(PitchAxis(hmd_state))),
            # wheel rotation is tracked up to 1/4 turn in either direction (i.e. 90 degrees)
            # note that we subtract the HMD roll, so you can tilt your entire body
            # left/right without it causing your vehicle to steer
            HID_USAGE_RZ: GatedAxis(0.5)(
                # you can toggle steering tracking by clicking the grip 3x
                NotButton(
                    ToggleButton(
                        MultiClickButton(0.5, 3)(
                            AndButton(
                                grip_button(left_controller_state),
                                grip_button(right_controller_state)
                            )
                        )
                    )
                ),
                ScaleAxis(
                    HALF_CIRCLE_ROTATION_SCALAR,
                    0.0)(
                    DifferenceAxis(
                        Wheel(
                            left_controller_state,
                            right_controller_state),
                        RollAxis(hmd_state)))
            ),
            HID_USAGE_SL0: ControllerAxis(1, 'x')(left_controller_state),  # left trigger
            HID_USAGE_SL1: ControllerAxis(1, 'x')(right_controller_state),  # right trigger
        }

    def trackpad_edge_buttons(self, controller_state: ControllerStateGenerator,
                              require_press=False) -> Iterable[Button]:
        base_buttons = [
            AxisThresholdButton(
                TOUCHPAD_EDGE_BUTTON_THRESHOLD,
                '>')(
                ControllerAxis(
                    0,
                    'y')(controller_state)),
            # touchpad top
            AxisThresholdButton(
                TOUCHPAD_EDGE_BUTTON_THRESHOLD,
                '>')(
                ControllerAxis(
                    0,
                    'x')(controller_state)),
            # touchpad right
            AxisThresholdButton(-TOUCHPAD_EDGE_BUTTON_THRESHOLD, '<')(ControllerAxis(0, 'y')
                                                                      (controller_state)),  # touchpad bottom
            AxisThresholdButton(-TOUCHPAD_EDGE_BUTTON_THRESHOLD, '<')(ControllerAxis(0, 'x')
                                                                      (controller_state)),  # touchpad left
        ]

        if require_press:
            return [AndButton(button, DirectButton(openvr.k_EButton_Axis0, 'press')(controller_state))
                    for button in base_buttons]

        return base_buttons

    def thumbstick_edge_buttons(self, controller_state: ControllerStateGenerator) -> Iterable[Button]:
        return [
            AxisThresholdButton(
                TOUCHPAD_EDGE_BUTTON_THRESHOLD,
                '>')(
                ControllerAxis(
                    2,
                    'y')(controller_state)),
            # thumbstick top
            AxisThresholdButton(
                TOUCHPAD_EDGE_BUTTON_THRESHOLD,
                '>')(
                ControllerAxis(
                    2,
                    'x')(controller_state)),
            # thumbstick right
            AxisThresholdButton(-TOUCHPAD_EDGE_BUTTON_THRESHOLD, '<')(ControllerAxis(2, 'y')
                                                                      (controller_state)),  # thumbstick bottom
            AxisThresholdButton(-TOUCHPAD_EDGE_BUTTON_THRESHOLD, '<')(ControllerAxis(2, 'x')
                                                                      (controller_state)),  # thumbstick left
        ]

    # fire gesture - activates with a strong tilt, but doesn't deactivate until tilt decreases significantly.
    @staticmethod
    def sticky_forward_tilt(grip: Button, controller_pitch: Axis, hmd_pitch: Axis) -> StickyPairButton:
        initiator = GestureButton(-TWIST_GESTURE_THRESHOLD, '<', sticky=False)(
            grip,
            DifferenceAxis(controller_pitch, hmd_pitch),
        )
        limiter = GestureButton(-TWIST_GESTURE_THRESHOLD / 2, '<', sticky=False)(
            grip,
            DifferenceAxis(controller_pitch, hmd_pitch),
        )

        return StickyPairButton(initiator, limiter)

    def generate_button_mapping(self, root_node: VrSystemState) -> dict[int, Button]:
        hmd_state = ControllerStateByType('hmd')(root_node)
        left_controller_state = ControllerStateByType('controller', 'left_hand')(root_node)
        right_controller_state = ControllerStateByType('controller', 'right_hand')(root_node)

        grip_button = DirectButton(openvr.k_EButton_Grip, 'press')

        left_controller_grip = grip_button(left_controller_state)
        right_controller_grip = grip_button(right_controller_state)

        hmd_pitch = PitchAxis(hmd_state)
        hmd_y = YAxis(hmd_state)
        hmd_z = ZAxis(hmd_state)

        left_controller_pitch = PitchAxis(left_controller_state)
        left_controller_roll = RollAxis(left_controller_state)
        left_controller_x = XAxis(left_controller_state)
        left_controller_y = YAxis(left_controller_state)
        left_controller_z = ZAxis(left_controller_state)

        right_controller_pitch = PitchAxis(right_controller_state)
        right_controller_roll = RollAxis(right_controller_state)
        right_controller_x = XAxis(right_controller_state)
        right_controller_y = YAxis(right_controller_state)
        right_controller_z = ZAxis(right_controller_state)

        # down-then-back gesture for handbrake
        l_pull_down_then_back_gesture = SequentialGesture(
            left_controller_grip,
            (-TRANSLATIONAL_GESTURE_THRESHOLD, DifferenceAxis(left_controller_y, hmd_y)),
            (TRANSLATIONAL_GESTURE_THRESHOLD, DifferenceAxis(left_controller_z, hmd_z))
        )

        r_push_down_then_forward_gesture = SequentialGesture(
            right_controller_grip,
            (-TRANSLATIONAL_GESTURE_THRESHOLD, DifferenceAxis(right_controller_y, hmd_y)),
            (-TRANSLATIONAL_GESTURE_THRESHOLD, DifferenceAxis(right_controller_z, hmd_z))
        )

        # CCW-CW-push gesture for mode switch
        r_ccw_cw_push_gesture = SequentialGesture(
            right_controller_grip,
            (TWIST_GESTURE_THRESHOLD, right_controller_roll),
            (-TWIST_GESTURE_THRESHOLD, right_controller_roll),
            (-TRANSLATIONAL_GESTURE_THRESHOLD * 5, right_controller_z)
        )

        # raise-left-right-left gesture for calling ship
        r_raise_l_r_l_gesture = SequentialGesture(
            right_controller_grip,
            (TRANSLATIONAL_GESTURE_THRESHOLD, right_controller_y),
            (-TRANSLATIONAL_GESTURE_THRESHOLD, right_controller_x),
            (TRANSLATIONAL_GESTURE_THRESHOLD, right_controller_x),
            (-TRANSLATIONAL_GESTURE_THRESHOLD, right_controller_x)
        )

        buttons = [
            l_pull_down_then_back_gesture,  # handbrake by pressing left grip, then pulling down and back
            # primary/secondary fire by pressing left/right grip and tilting controller forward
            self.sticky_forward_tilt(left_controller_grip, left_controller_pitch, hmd_pitch),
            self.sticky_forward_tilt(right_controller_grip, right_controller_pitch, hmd_pitch),
            CircleGesture(
                True,
                TRANSLATIONAL_GESTURE_THRESHOLD,
                left_controller_x,
                left_controller_y,
                left_controller_grip),
            # buttons triggered by touching the edges of the left trackpad
            *self.trackpad_edge_buttons(left_controller_state, True),
            # buttons triggered by touching the edges of the right trackpad
            *self.trackpad_edge_buttons(right_controller_state, True),
            *self.thumbstick_edge_buttons(right_controller_state),
            # buttons triggered by the cardinal directions of the right thumbstick
            DirectButton(openvr.k_EButton_Axis2, 'press')(left_controller_state),  # thumbstick presses
            DirectButton(openvr.k_EButton_Axis2, 'press')(right_controller_state),
            DirectButton(openvr.k_EButton_ApplicationMenu, 'press')(left_controller_state),  # menu buttons
            DirectButton(openvr.k_EButton_ApplicationMenu, 'press')(right_controller_state),
            r_ccw_cw_push_gesture,
            r_raise_l_r_l_gesture,
            r_push_down_then_forward_gesture
        ]

        return {
            i + 1: button
            for i, button in enumerate(buttons)
        }

    def generate_event_triggers(self, root_node: VrSystemState) -> list[ValueConsumer]:
        left_controller_state = ControllerStateByType('controller', 'left_hand')(root_node)
        right_controller_state = ControllerStateByType('controller', 'right_hand')(root_node)

        grip_button = DirectButton(openvr.k_EButton_Grip, 'press')

        return [
            HapticPulseTrigger(root_node.device_id_for_type('controller', 'left_hand'), {'just_pressed', 'just_unpressed'})(
                root_node.vr_system,
                MultiClickButton(0.5, 3)(
                    AndButton(
                        grip_button(left_controller_state),
                        grip_button(right_controller_state)
                    )
                )
            ),
            HapticPulseTrigger(root_node.device_id_for_type('controller', 'right_hand'), {'just_pressed', 'just_unpressed'})(
                root_node.vr_system,
                MultiClickButton(0.5, 3)(
                    AndButton(
                        grip_button(left_controller_state),
                        grip_button(right_controller_state)
                    )
                )
            )
        ]
