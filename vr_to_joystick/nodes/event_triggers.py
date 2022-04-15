from typing import Any, Hashable

from openvr import VRSystem

from vr_to_joystick.nodes.types import Button, ButtonTickState
from vr_to_joystick.nodes.value_generator import ValueConsumer


class HapticPulse(ValueConsumer):
    requirements = {'parent_button'}

    def __init__(self, vr_system: VRSystem, parent_button: Button):
        super().__init__(dependencies={'parent_button': parent_button})
        self.vr_system = vr_system


def HapticPulseTrigger(controller_id: int, pulse_events: set[ButtonTickState],
                       duration_mcs: int = 1000) -> type[HapticPulse]:
    class _ConfiguredHapticPulseTrigger(HapticPulse):
        @classmethod
        def _parameterized_on(cls) -> list[Hashable]:
            return [controller_id, tuple(pulse_events)]

        def update_with_inputs(self, inputs: dict[str, Any]) -> None:
            if inputs['parent_button']['tick_state'] in pulse_events:
                self.vr_system.triggerHapticPulse(controller_id, 0, duration_mcs)

    return _ConfiguredHapticPulseTrigger
