# -*- coding: utf-8 -*-
import struct
import select
import threading
import fcntl
import os
from enum import Enum

# struct input_event {
        # struct timeval time;
        # unsigned short type;
        # unsigned short code;
        # unsigned int value;
# };

event_struct = "@llHHi"
event_size = struct.calcsize(event_struct)

EV_SYN = 0x00
EV_KEY = 0x01
EV_REL = 0x02
EV_ABS = 0x03
EV_MSC = 0x04
EV_SW = 0x05
EV_LED = 0x11
EV_SND = 0x12
EV_REP = 0x14
EV_FF = 0x15
EV_PWR = 0x16
EV_FF_STATUS = 0x17

class Direction(Enum):
    CW = 1
    CCW = -1

class ButtonPos(Enum):
    KeyDown = 1
    KeyUp = 0

def do_nothing(a):
    pass

class Powermate(threading.Thread):
    def __init__(self, turn_listener=do_nothing, click_listener=do_nothing):
        super(Powermate,self).__init__()
        self.fd = -1
        if not self.open_dev():
            raise RuntimeError("Unable to open input device")
        self.take_over()
        self.onclick = click_listener
        self.onturn = turn_listener
        self.start()

    def __del__(self):
        if self.fd >= 0:
            os.close(self.fd)

    def take_over(self):
        fcntl.ioctl(self.fd, 0x40044590, 1)

    def open_dev(self):
        try:
            base_dir = "/dev/input/by-id"
            flist = [f for f in os.listdir(base_dir) if "Griffin" in f]
            if flist:
                fname = os.path.join(base_dir, flist[0])
            else:
                return False
            self.fd = os.open(fname, os.O_RDWR)
            if self.fd < 0:
                return False
            # Read the device name
            name = fcntl.ioctl(self.fd,  0x80ff4506, chr(0) * 256)
            name = name.split(b'\0',1)[0].decode("utf-8")
            print(name)
            if "griffin powermate" in name.lower():
                fcntl.fcntl(self.fd, fcntl.F_SETFL, os.O_NDELAY)
                return True
            os.close(self.fd)
            return False
        except OSError:
            return False

    def set_onturn(self, listener):
        self.onturn = listener

    def set_onclick(self, listener):
        self.onclick = listener

    def run(self):
        while True:
            # wait for there to be input available
            select.select([self.fd],[],[])
            event = os.read(self.fd, event_size)
            unpacked_event = struct.unpack(event_struct, event)
            time_secs, time_ms, ev_type, code, value = unpacked_event
            if ev_type == EV_REL:
                self.onturn(Direction(value))
            if ev_type == EV_KEY:
                self.onclick(ButtonPos(value))


if __name__ == '__main__':
    def on_turn(direction):
        print(direction)
    def on_click(button_pos):
        print(button_pos)
    p = Powermate(on_turn, on_click)
    # p.join()
