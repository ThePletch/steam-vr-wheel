from typing import Hashable

from vr_to_joystick.mappings.nodes.types import BaseButton, ButtonEventType, ButtonState
from vr_to_joystick.mappings.nodes.vr_system_state import ControllerStateConsumer, ControllerStatePackage


# Basic button class. Reads the current value of an actual button on the controller.
def DirectButton(button_id: int, event_type: ButtonEventType) -> type[ControllerStateConsumer[ButtonState]]:
    class _ConfiguredButton(ControllerStateConsumer[ButtonState], BaseButton):

        @classmethod
        def _parameterized_on(cls) -> list[Hashable]:
            return [button_id, event_type]

        def get_button_state_this_tick(self, inputs: dict[str, ControllerStatePackage]) -> bool:
            button_states = inputs['base_state']['button_state']
            if event_type == 'press':
                target_states = button_states['pressed']
            else:
                target_states = button_states['touched']

            return target_states[button_id]

    return _ConfiguredButton
