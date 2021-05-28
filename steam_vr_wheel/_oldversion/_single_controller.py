import math

import openvr

from steam_vr_wheel.pyvjoy.vjoydevice import HID_USAGE_X, HID_USAGE_Y, HID_USAGE_Z, HID_USAGE_RX, HID_USAGE_RY, HID_USAGE_RZ, HID_USAGE_SL0, HID_USAGE_SL1
from steam_vr_wheel._virtualpad import VirtualPad, RightTrackpadAxisDisablerMixin, LeftTrackpadAxisDisablerMixin

class SingleController(RightTrackpadAxisDisablerMixin, LeftTrackpadAxisDisablerMixin, VirtualPad):
    LATERAL_SCALAR = 2

    TRIGGER = 1
    GRIP = 2
    MENU = 3
    TRACKPAD_TOUCH = 4
    TRACKPAD_MIDPRESS = 5

    THUMBSTICK_DIRBUTTON_THRESHOLD = 0.8

    def __init__(self):
        super().__init__()
        self.trackpadBaselineX = None
        self.trackpadBaselineY = None
        self.baselineX = None
        self.baselineY = None
        self.baselineZ = None
        self.baselineRX = None
        self.baselineRY = None
        self.baselineRZ = None
    
    def get_roll(self, ctr):
        return ctr.roll/180 + 1
    
    def get_pitch(self, ctr):
        return ctr.pitch/180 + 1
    
    def get_yaw(self, ctr):
        return ctr.yaw/180 + 1
    
    def updateTrackpadByOffset(self, ctr):
        if self.pressed_buttons[self.TRACKPAD_TOUCH]:
            if not (self.trackpadBaselineX and self.trackpadBaselineY):
                self.trackpadBaselineX = ctr.trackpadX
                self.trackpadBaselineY = ctr.trackpadY
            self.trackpadX = ctr.trackpadX
            self.trackpadY = ctr.trackpadY

            xDelta = self.trackpadX - self.trackpadBaselineX
            yDelta = self.trackpadY - self.trackpadBaselineY
            self.device.set_axis(HID_USAGE_SL0, int((xDelta + 0.5) * 0x8000))
            self.device.set_axis(HID_USAGE_SL1, int((yDelta + 0.5) * 0x8000))
        else:
            self.trackpadBaselineX = None
            self.trackpadBaselineY = None
            self.device.set_axis(HID_USAGE_SL0, int(0.5 * 0x8000))
            self.device.set_axis(HID_USAGE_SL1, int(0.5 * 0x8000))
    
    def updateThumbstickButtons(self, ctr):
        def buttonizeAxis(axis, threshold, posButtonId, negButtonId):
            self.button_update(posButtonId, axis > threshold)
            self.button_update(negButtonId, axis < -threshold)

        # self.device.set_axis(HID_USAGE_SL0, int((ctr.thumbstickX + 0.5) * 0x8000))
        # self.device.set_axis(HID_USAGE_SL1, int((ctr.thumbstickY + 0.5) * 0x8000))

        buttonizeAxis(ctr.thumbstickX, self.THUMBSTICK_DIRBUTTON_THRESHOLD, 10, 12)
        buttonizeAxis(ctr.thumbstickY, self.THUMBSTICK_DIRBUTTON_THRESHOLD, 11, 13)
    
    def updateLateralByOffset(self, ctr):
        if self.pressed_buttons[self.TRIGGER]:
            if not (self.baselineX and self.baselineY and self.baselineZ):
                self.baselineX = ctr.x
                self.baselineY = ctr.y
                self.baselineZ = ctr.z

            xDelta = ctr.x - self.baselineX
            yDelta = ctr.y - self.baselineY
            zDelta = ctr.z - self.baselineZ
            self.device.set_axis(HID_USAGE_X, int((xDelta * self.LATERAL_SCALAR + 0.5) * 0x8000))
            self.device.set_axis(HID_USAGE_Y, int((yDelta * self.LATERAL_SCALAR + 0.5) * 0x8000))
            self.device.set_axis(HID_USAGE_Z, int((zDelta * self.LATERAL_SCALAR + 0.5) * 0x8000))
        else:
            self.baselineX = None
            self.baselineY = None
            self.baselineZ = None
            self.device.set_axis(HID_USAGE_X, int(0.5 * 0x8000))
            self.device.set_axis(HID_USAGE_Y, int(0.5 * 0x8000))
            self.device.set_axis(HID_USAGE_Z, int(0.5 * 0x8000))
    
    def updateRotationByOffset(self, ctr):
        def deboinkDelta(current, baseline):
            rawDelta = (current - baseline) % 2
            if rawDelta > 1:
                return -(2 - rawDelta)
            return rawDelta
            
        if self.pressed_buttons[self.TRIGGER]:
            if not (self.baselineRX and self.baselineRY and self.baselineRZ):
                self.baselineRX = self.get_pitch(ctr)
                self.baselineRY = self.get_roll(ctr)
                self.baselineRZ = self.get_yaw(ctr)

            xDelta = deboinkDelta(self.get_pitch(ctr), self.baselineRX)
            yDelta = deboinkDelta(self.get_roll(ctr), self.baselineRY)
            zDelta = deboinkDelta(self.get_yaw(ctr), self.baselineRZ)
            self.device.set_axis(HID_USAGE_RX, int((xDelta + 0.5) * 0x8000))
            self.device.set_axis(HID_USAGE_RY, int((yDelta + 0.5) * 0x8000))
            self.device.set_axis(HID_USAGE_RZ, int((zDelta + 0.5) * 0x8000))
        else:
            self.baselineRX = None
            self.baselineRY = None
            self.baselineRZ = None
            self.device.set_axis(HID_USAGE_RX, int(0.5 * 0x8000))
            self.device.set_axis(HID_USAGE_RY, int(0.5 * 0x8000))
            self.device.set_axis(HID_USAGE_RZ, int(0.5 * 0x8000))

    def update(self, ctr):
        self.updateTrackpadByOffset(ctr)
        self.updateLateralByOffset(ctr)
        self.updateRotationByOffset(ctr)
        self.updateThumbstickButtons(ctr)
        self.trackpadX = ctr.trackpadX
        self.trackpadY = ctr.trackpadY