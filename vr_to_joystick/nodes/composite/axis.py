from abc import abstractmethod
from typing import Any

from vr_to_joystick.mappings.nodes.types import Axis, Button


class SwitchAxis(Axis):
    requirements = {'switch_button', 'off_axis', 'on_axis'}

    def __init__(self, switch_button: Button, off_axis: Axis, on_axis: Axis):
        super().__init__(dependencies={'switch_button': switch_button, 'off_axis': off_axis, 'on_axis': on_axis})

    def generate_output(self, inputs: dict[str, Any]) -> float:
        if inputs['switch_button']['active']:
            return inputs['on_axis']  # type: ignore

        return inputs['off_axis']  # type: ignore


class PairAxis(Axis):
    requirements = {'axis_a', 'axis_b'}

    def __init__(self, axis_a: Axis, axis_b: Axis):
        super().__init__(dependencies={'axis_a': axis_a, 'axis_b': axis_b})

    @abstractmethod
    def combine_states(self, axis_a: float, axis_b: float) -> float:
        pass

    def generate_output(self, inputs: dict[str, Any]) -> float:
        return self.combine_states(inputs['axis_a'], inputs['axis_b'])


class SumAxis(PairAxis):
    def combine_states(self, axis_a: float, axis_b: float) -> float:
        return axis_a + axis_b


class DifferenceAxis(PairAxis):
    def combine_states(self, axis_a: float, axis_b: float) -> float:
        return axis_a - axis_b


class ProductAxis(PairAxis):
    def combine_states(self, axis_a: float, axis_b: float) -> float:
        return axis_a * axis_b


class QuotientAxis(PairAxis):
    def combine_states(self, axis_a: float, axis_b: float) -> float:
        return axis_a / axis_b


class MaxAxis(PairAxis):
    def combine_states(self, axis_a: float, axis_b: float) -> float:
        return max(axis_a, axis_b)


class MinAxis(PairAxis):
    def combine_states(self, axis_a: float, axis_b: float) -> float:
        return min(axis_a, axis_b)


class InvertedAxis(Axis):
    requirements = {'parent_axis'}

    def __init__(self, parent_axis: Axis):
        super().__init__(dependencies={'parent_axis': parent_axis})

    def generate_output(self, inputs: dict[str, Any]) -> float:
        return -1 * inputs['parent_axis']  # type: ignore


class MeanAxis(PairAxis):
    def combine_states(self, axis_a: float, axis_b: float) -> float:
        return (axis_a + axis_b) / 2
