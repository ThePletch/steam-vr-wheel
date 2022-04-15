from functools import reduce
import time
from typing import Any, Callable, Hashable, Literal, Union

from vr_to_joystick.nodes.axis_helpers import DeltaAxis
from vr_to_joystick.nodes.composite.button import AndButton, StickyPairButton
from vr_to_joystick.nodes.types import Axis, BaseButton, Button


Comparator = Literal['<', '<=', '>', '>=']


# Button that toggles on and off when another button is pressed
class ToggleButton(BaseButton):
    requirements = {'parent_button'}

    def __init__(self, parent_button: Button):
        super().__init__(dependencies={'parent_button': parent_button})

    def get_button_state_this_tick(self, inputs: dict[str, Any]) -> bool:
        if inputs['parent_button']['tick_state'] == 'just_pressed':
            return not self.state

        return self.state


# A button that is active when an axis's value exceeds the specified threshold.
def AxisThresholdButton(threshold: float, comparator: Comparator) -> type[Button]:
    class _ConfiguredAxisThresholdButton(BaseButton):
        requirements = {'parent_axis'}

        def __init__(self, parent_axis: Axis):
            super().__init__(dependencies={'parent_axis': parent_axis})

        @classmethod
        def _parameterized_on(cls) -> list[Hashable]:
            return [threshold, comparator]

        def comparator_function(self) -> Callable[[float], bool]:
            return {
                '<': lambda x: x < threshold,
                '<=': lambda x: x <= threshold,
                '>': lambda x: x > threshold,
                '>=': lambda x: x >= threshold,
            }[comparator]

        def get_button_state_this_tick(self, inputs: dict[str, Any]) -> bool:
            return self.comparator_function()(inputs['parent_axis'])

    return _ConfiguredAxisThresholdButton


# todo make this less broad
Gesture = Union[StickyPairButton, AndButton]

# button that activates when you press and hold the specified button before moving the specified axis the given amount.
# Once you've performed a gesture, if sticky is set to true, the button remains active until you release the activation button.
# If sticky is set to false, the gesture will also end when the axis threshold is no longer met.


def GestureButton(threshold: float, comparator: Comparator, sticky: bool = True) -> Callable[[Button, Axis], Gesture]:
    def ComposeGestureButton(activation_button: Button, gesture_axis: Axis) -> Gesture:
        axis_action = AxisThresholdButton(threshold, comparator)(DeltaAxis(activation_button, gesture_axis))

        if sticky:
            return StickyPairButton(axis_action, activation_button)

        return AndButton(axis_action, activation_button)

    return ComposeGestureButton

# Produces a gesture that recognizes the listed gestures performed in sequence.
# Each step is specified as an amount of movement and the axis along which to measure that movement.


def SequentialGesture(activation_button: Button, *gestures: tuple[float, Axis]) -> Button:
    def comparator_for_gesture_threshold(threshold: float) -> Comparator:
        if threshold < 0:
            return '<'
        return '>'

    def extend_gesture_with_step(gesture: Button, gesture_config: tuple[float, Axis]) -> Gesture:
        return GestureButton(
            gesture_config[0],
            comparator_for_gesture_threshold(gesture_config[0])
        )(gesture, gesture_config[1])

    return reduce(extend_gesture_with_step, gestures, activation_button)


# Gesture that recognizes moving in a circle. Assumes that the circle begins at the top.
# To recognize circular movement independent of its starting point, use an OrButton to chain four of these together,
# each recognizing a different starting point. I don't recommend this.
def CircleGesture(clockwise: bool, size: float, x_axis: Axis, y_axis: Axis, activate_button: Button) -> Button:
    leftright_size = (1 if clockwise else -1) * size
    return SequentialGesture(
        activate_button,           # clockwise directions:
        (leftright_size, x_axis),       # right
        (-1 * size, y_axis),  # down
        (-1 * leftright_size, x_axis),  # left
        (size, y_axis)        # up
    )


# Button that activates only when its parent button is pressed a given number of times within the specified interval.
# Stays active as long as the button is pressed once it registers the final press.
# Will continue to activate for presses beyond the required minimum, if
# the user continues to press at intervals less than the maximum.
def MultiClickButton(max_click_interval_seconds: float, required_clicks: int = 2) -> type[Button]:
    class _ConfiguredMultiClickButton(BaseButton):
        requirements = {'parent_button'}

        last_click_recorded: float
        clicks_seen: int

        def __init__(self, parent_button: Button):
            super().__init__(dependencies={'parent_button': parent_button})
            self.last_click_recorded = -1
            self.clicks_seen = 0

        @classmethod
        def _parameterized_on(cls) -> list[Hashable]:
            return [max_click_interval_seconds, required_clicks]

        def get_button_state_this_tick(self, inputs: dict[str, Any]) -> bool:
            if inputs['parent_button']['tick_state'] == 'just_pressed':
                current_time = time.time()
                if (current_time - self.last_click_recorded) > max_click_interval_seconds:
                    self.clicks_seen = 0
                self.last_click_recorded = current_time
                self.clicks_seen += 1

            return self.clicks_seen >= required_clicks and inputs['parent_button']['active']

    return _ConfiguredMultiClickButton
