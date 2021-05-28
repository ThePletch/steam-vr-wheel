import math
from typing import Any, Hashable, Literal

from steam_vr_wheel.mappings.nodes.vr_system_state import ControllerState, ControllerStateConsumer
from steam_vr_wheel.mappings.nodes.value_generator import ValueGenerator

Axis = ValueGenerator[float]

DirectAxis = ControllerStateConsumer[float]


def TranslationalAxis(pose_index: int) -> type[DirectAxis]:
    class _ConfiguredTranslationalAxis(DirectAxis):
        @classmethod
        def _parameterized_on(cls) -> list[Hashable]:
            return [pose_index]

        def generate_output(self, inputs: dict[str, Any]) -> float:
            return inputs['base_state']['pose'][pose_index][3]  # type: ignore
    
    return _ConfiguredTranslationalAxis


XAxis = TranslationalAxis(0)
YAxis = TranslationalAxis(1)
ZAxis = TranslationalAxis(2)

AxisName = Literal['x', 'y', 'z']

def VelocityAxis(axis_name: AxisName) -> type[DirectAxis]:
    axis_index = {
        'x': 0,
        'y': 1,
        'z': 2,
    }[axis_name]

    class _ConfiguredVelocityAxis(DirectAxis):
        @classmethod
        def _parameterized_on(cls) -> list[Hashable]:
            return [axis_index]

        def generate_output(self, inputs: dict[str, Any]) -> float:
            return inputs['base_state']['velocity'][axis_index]  # type: ignore
    
    return _ConfiguredVelocityAxis


VXAxis = VelocityAxis('x')
VYAxis = VelocityAxis('y')
VZAxis = VelocityAxis('z')


class YawAxis(DirectAxis):
    def generate_output(self, inputs: dict[str, Any]) -> float:
        return -1 * math.asin(inputs['base_state']['pose'][2][0])

class PitchAxis(DirectAxis):
    def generate_output(self, inputs: dict[str, Any]) -> float:
        pose = inputs['base_state']['pose']

        return math.atan2(pose[2][1], pose[2][2])


class RollAxis(DirectAxis):
    def generate_output(self, inputs: dict[str, Any]) -> float:
        pose = inputs['base_state']['pose']

        return math.atan2(pose[1][0], pose[0][0])

ControllerAxisType = Literal['x', 'y']

# an axis read from the controller's inputs rather than its position in space
def ControllerAxis(axis_index: int, axis_type: ControllerAxisType = 'x') -> type[DirectAxis]:
    class _ConfiguredControllerAxis(DirectAxis):
        @classmethod
        def _parameterized_on(cls) -> list[Hashable]:
            return [axis_index, axis_type]

        def generate_output(self, inputs: dict[str, Any]) -> float:
            raxis = inputs['base_state']['controller_state'].rAxis[axis_index]

            if axis_type == 'x':
                return raxis.x  # type: ignore
            
            return raxis.y  # type: ignore
    
    return _ConfiguredControllerAxis