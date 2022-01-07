from abc import abstractmethod
from typing import Any
from steam_vr_wheel.mappings.nodes.button import BaseButton, Button, ButtonState


# Toggles between reporting the status of two buttons depending on the status of a third button
class SwitchButton(BaseButton):
    requirements = {'switch_button', 'off_button', 'on_button'}
    dependencies: dict[str, Button]

    def __init__(self, switch_button: Button, off_button: Button, on_button: Button):
        super().__init__(
            dependencies={
                'switch_button': switch_button,
                'off_button': off_button,
                'on_button': on_button})

    def get_button_state_this_tick(self, inputs: dict[str, ButtonState]) -> bool:
        if inputs['switch_button']['active']:
            return inputs['on_button']['active']
        return inputs['off_button']['active']


class PairButton(BaseButton):
    requirements = {'button_a', 'button_b'}

    def __init__(self, button_a: Button, button_b: Button):
        super().__init__(dependencies={'button_a': button_a, 'button_b': button_b})

    @abstractmethod
    def combine_states(self, button_a: ButtonState, button_b: ButtonState) -> bool:
        pass

    def get_button_state_this_tick(self, inputs: dict[str, Any]) -> bool:
        return self.combine_states(inputs['button_a'], inputs['button_b'])

# Button that turns on when both buttons are active, but doesn't turn off
# until both buttons turn off.


class StickyPairButton(PairButton):
    def __init__(self, button_a: Button, button_b: Button):
        super().__init__(button_a, button_b)
        self.currently_active = False

    def combine_states(self, button_a: ButtonState, button_b: ButtonState) -> bool:
        button_a_state = button_a['active']
        button_b_state = button_b['active']
        if self.currently_active:
            self.currently_active = button_a_state or button_b_state
        else:
            self.currently_active = button_a_state and button_b_state

        return self.currently_active


class AndButton(PairButton):
    def combine_states(self, button_a: ButtonState, button_b: ButtonState) -> bool:
        return button_a['active'] and button_b['active']


class OrButton(PairButton):
    def combine_states(self, button_a: ButtonState, button_b: ButtonState) -> bool:
        return button_a['active'] or button_b['active']


class XorButton(PairButton):
    def combine_states(self, button_a: ButtonState, button_b: ButtonState) -> bool:
        return button_a['active'] ^ button_b['active']


class NotButton(BaseButton):
    requirements = {'parent_button'}

    def __init__(self, parent_button: Button):
        super().__init__(dependencies={'parent_button': parent_button})

    def get_button_state_this_tick(self, inputs: dict[str, Any]) -> bool:
        return not inputs['parent_button']['active']
