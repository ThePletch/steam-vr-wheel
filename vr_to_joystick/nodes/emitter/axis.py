from typing import Any

from vr_to_joystick.mappings.nodes.types import Axis


# n.b. for consistency's sake, we may want this to still follow the class factory pattern
class ConstantAxis(Axis):
    value: float

    def __init__(self, value: float):
        super().__init__()
        self.value = value

    def generate_output(self, _: Any) -> float:
        return self.value
