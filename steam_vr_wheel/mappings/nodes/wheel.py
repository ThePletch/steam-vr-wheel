import math
from typing import Any
from steam_vr_wheel.mappings.nodes.axis import Axis
from steam_vr_wheel.mappings.nodes.vr_system_state import ControllerStateGenerator


# Axis that reports the angle between a left and right controller.
class Wheel(Axis):
    requirements = {'left_controller', 'right_controller'}

    def __init__(self, left_controller: ControllerStateGenerator, right_controller: ControllerStateGenerator):
        super().__init__(dependencies={'left_controller': left_controller, 'right_controller': right_controller})

    def generate_output(self, inputs: dict[str, Any]) -> float:
        # compute angle in Z plane between two controllers
        dx = inputs['right_controller']['pose'][0][3] - \
            inputs['left_controller']['pose'][0][3]  # x distance from left to right
        dy = inputs['right_controller']['pose'][1][3] - \
            inputs['left_controller']['pose'][1][3]  # y distance from left to right
        return math.atan2(dy, dx)
