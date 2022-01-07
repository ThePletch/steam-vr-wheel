from typing import Any, Hashable, Type

from vr_to_joystick.mappings.nodes.types import Axis, Button


class AxisMutator(Axis):
    requirements = {'parent_axis'}

    def __init__(self, parent_axis: Axis):
        super().__init__(dependencies={'parent_axis': parent_axis})

    def generate_output(self, inputs: dict[str, float]) -> float: ...


# Slides, then scales the given axis based on the factor and zero point given.
# Meant for use scaling an axis to the 0-to-1 range that VJoy expects, with the axis's zero point at 0.5
def ScaleAxis(scaling_factor: float, zero_point: float, resulting_zero_point: float = 0.5) -> type[AxisMutator]:
    class _ConfiguredScaleAxis(AxisMutator):
        @classmethod
        def _parameterized_on(cls) -> list[Hashable]:
            return [scaling_factor, zero_point, resulting_zero_point]

        def generate_output(self, inputs: dict[str, float]) -> float:
            return (inputs['parent_axis'] - zero_point) * scaling_factor + resulting_zero_point

    return _ConfiguredScaleAxis


# shift an axis's potential values by some amount, wrapping any values at the top to the bottom
def AxisShifter(axis_min: float, axis_max: float, shift_amount: float) -> type[AxisMutator]:
    class _ConfiguredAxisShifter(AxisMutator):
        @classmethod
        def _parameterized_on(cls) -> list[Hashable]:
            return [axis_min, axis_max, shift_amount]

        def generate_output(self, inputs: dict[str, float]) -> float:
            axis_range = axis_max - axis_min

            return (inputs['parent_axis'] - axis_min + shift_amount) % axis_range + axis_min

    return _ConfiguredAxisShifter


# if an axis exceeds the specified range, report the edge of the range instead of the axis value
def AxisClamp(axis_min: float, axis_max: float) -> type[AxisMutator]:
    class _ConfiguredAxisClamp(AxisMutator):
        @classmethod
        def _parameterized_on(cls) -> list[Hashable]:
            return [axis_min, axis_max]

        def generate_output(self, inputs: dict[str, float]) -> float:
            return min(axis_max, max(inputs['parent_axis'], axis_min))

    return _ConfiguredAxisClamp


def DeadzoneAxis(deadzone: float) -> type[AxisMutator]:
    class _ConfiguredDeadzoneAxis(AxisMutator):
        @classmethod
        def _parameterized_on(cls) -> list[Hashable]:
            return [deadzone]

        def generate_output(self, inputs: dict[str, float]) -> float:
            if abs(inputs['parent_axis']) < deadzone:
                return 0.0

            return inputs['parent_axis']

    return _ConfiguredDeadzoneAxis


# Axis that is reset to zero when the specified button is pressed.
class ResettableAxis(Axis):
    requirements = {'reset_button', 'parent_axis'}

    baseline_value: float

    def __init__(self, reset_button: Button, parent_axis: Axis):
        self.baseline_value = 0.0
        super().__init__(dependencies={'reset_button': reset_button, 'parent_axis': parent_axis})

    def generate_output(self, inputs: dict[str, Any]) -> float:
        if inputs['reset_button']['tick_state'] == 'just_pressed':
            self.baseline_value = inputs['parent_axis']

        return inputs['parent_axis'] - self.baseline_value  # type: ignore  # todo make input dicts more restrictive


# Axis that reports a value only when the specified button is active.
def GatedAxis(disabled_value: float = 0.0) -> Type[Axis]:
    class _ConfiguredGatedAxis(Axis):
        requirements = {'gate_button', 'parent_axis'}

        @classmethod
        def _parameterized_on(cls) -> list[Hashable]:
            return [disabled_value]

        def __init__(self, gate_button: Button, parent_axis: Axis):
            super().__init__(dependencies={'gate_button': gate_button, 'parent_axis': parent_axis})

        def generate_output(self, inputs: dict[str, Any]) -> float:
            if inputs['gate_button']['active']:
                return inputs['parent_axis']  # type: ignore

            return disabled_value

    return _ConfiguredGatedAxis


# Composition of GatedAxis and ResettableAxis pointed at the same button.
# Whenever the button is pressed, the axis is zeroed out and reports any
# change in its value until the button is released.
def DeltaAxis(button: Button, parent_axis: Axis) -> Axis:
    return GatedAxis(disabled_value=0)(button, ResettableAxis(button, parent_axis))


class PushPullAxis(Axis):

    requirements = {'enable_delta_button', 'delta_axis'}

    baseline_value: float
    modified_value: float

    def __init__(self, enable_delta_button: Button, parent_axis: Axis):
        self.baseline_value = 0.0
        self.modified_value = 0.0
        super().__init__(
            dependencies={
                'enable_delta_button': enable_delta_button,
                'delta_axis': DeltaAxis(
                    enable_delta_button,
                    parent_axis)})

    def generate_output(self, inputs: dict[str, Any]) -> float:
        delta_button_tick_state = inputs['enable_delta_button']['tick_state']
        if delta_button_tick_state == 'just_unpressed':
            self.baseline_value = self.modified_value
        elif inputs['enable_delta_button']['active']:
            self.modified_value = self.baseline_value + inputs['delta_axis']

        return self.modified_value
