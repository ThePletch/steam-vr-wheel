from abc import abstractmethod
from typing import Any, Literal, TypedDict

from steam_vr_wheel.mappings.nodes.value_generator import ValueGenerator

Axis = ValueGenerator[float]

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
