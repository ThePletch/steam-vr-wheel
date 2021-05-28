
from steam_vr_wheel.mappings.test_mapping import TestController
from steam_vr_wheel.mappings.wheel_mapping import WheelMapping
import time

import openvr

FREQUENCY = 30


def main() -> None:
    openvr.init(openvr.VRApplication_Overlay)
    vrsystem = openvr.VRSystem()
    TICK_SECONDS = 1/FREQUENCY
    
    # test_mapping = StandardController(vrsystem, 3)
    # test_mapping = ThrottleMapping(vrsystem, 3)
    test_mapping = TestController(vrsystem, 3)
    while True:
        before_work = time.time()
        test_mapping.tick()
        after_work = time.time()
        left = TICK_SECONDS - (after_work - before_work)
        if left > 0:
            time.sleep(left)

if __name__ == '__main__':
    main()
