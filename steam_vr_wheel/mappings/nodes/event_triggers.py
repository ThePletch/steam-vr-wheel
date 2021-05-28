from typing import Any, Hashable

from openvr import VRSystem
from steam_vr_wheel.mappings.nodes.button import Button, ButtonTickState
from steam_vr_wheel.mappings.nodes.value_generator import ValueConsumer


def HapticPulseTrigger(controller_id, pulse_events: set[ButtonTickState],
                       duration_mcs: int = 1000) -> type[ValueConsumer]:
    class _ConfiguredHapticPulseTrigger(ValueConsumer):
        requirements = {'parent_button'}

        @classmethod
        def _parameterized_on(cls) -> list[Hashable]:
            return [controller_id, pulse_events]

        def __init__(self, vr_system: VRSystem, parent_button: Button):
            super().__init__(dependencies={'parent_button': parent_button})
            self.vr_system = vr_system

        def update_with_inputs(self, inputs: dict[str, Any]) -> None:
            if inputs['parent_button']['tick_state'] in pulse_events:
                self.vr_system.triggerHapticPulse(controller_id, 0, duration_mcs)

    return _ConfiguredHapticPulseTrigger
