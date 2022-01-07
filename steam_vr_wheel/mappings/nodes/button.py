from abc import abstractmethod
from typing import Any, Hashable, Literal, TypedDict

from steam_vr_wheel.mappings.nodes.vr_system_state import ControllerStateConsumer, ControllerStatePackage
from steam_vr_wheel.mappings.nodes.value_generator import ValueGenerator

ButtonEventType = Literal['touch', 'press']
ButtonTickState = Literal[
    'active',          # button is pressed and was pressed last tick
    'just_unpressed',  # button is not pressed but was pressed last tick
    'inactive',        # button is not pressed and was not pressed last tick
    'just_pressed',    # button is pressed but was not pressed last tick
]


class ButtonState(TypedDict):
    active: bool
    tick_state: ButtonTickState


Button = ValueGenerator[ButtonState]

TICK_STATE_MAPPING: dict[tuple[bool, bool], ButtonTickState] = {
    (False, False): 'inactive',
    (False, True): 'just_pressed',
    (True, False): 'just_unpressed',
    (True, True): 'active',
}


class BaseButton(Button):
    state: bool

    def __init__(
        self,
        *,
        dependencies: dict[str, ValueGenerator[Any]] = {}
    ):
        super().__init__(dependencies=dependencies)
        self.state = False

    @abstractmethod
    def get_button_state_this_tick(self, inputs: dict[str, Any]) -> bool:
        pass

    def generate_output(self, inputs: dict[str, Any]) -> ButtonState:
        new_state = self.get_button_state_this_tick(inputs)

        tick_state = TICK_STATE_MAPPING[(self.state, new_state)]

        self.state = new_state

        return ButtonState(active=new_state, tick_state=tick_state)


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
