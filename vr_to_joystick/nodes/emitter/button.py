import time
from typing import Any

from vr_to_joystick.nodes.types import BaseButton


class AlwaysOffButton(BaseButton):
    def get_button_state_this_tick(self, _: Any) -> bool:
        return False


class AlwaysOnButton(BaseButton):
    def get_button_state_this_tick(self, _: Any) -> bool:
        return True


# Button turns off for one tick every time the configured interval elapses.
# Useful for gestures that are always listening, to allow the gesture to turn back off.
class FlickeringButton(BaseButton):
    interval: float
    last_flicker: float

    def __init__(self, interval: float):
        super().__init__()
        self.interval = interval
        self.last_flicker = 0

    def get_button_state_this_tick(self, _: Any) -> bool:
        current_time = time.time()
        if (current_time - self.last_flicker) > self.interval and self.state:
            self.last_flicker = current_time
            return False

        return True
