from typing import Any, Hashable

from vr_to_joystick.nodes.types import BaseButton, Button, ButtonState
from vr_to_joystick.nodes.vr_system_state import ControllerStateConsumer


# Button activated when the controller moves faster than the given threshold (in meters per second)
def Flick(threshold: float) -> type[Button]:
    class _ConfiguredFlick(ControllerStateConsumer[ButtonState], BaseButton):
        @classmethod
        def _parameterized_on(cls) -> list[Hashable]:
            return [threshold]

        def get_button_state_this_tick(self, inputs: dict[str, Any]) -> bool:
            return max(abs(v) for v in inputs['base_state']['velocity']) > threshold

    return _ConfiguredFlick
