from .notepad import *

__version__ = "0.1.2"

def autodetect():
    for devType in ('12fx', '8fx', '5'):
        dev = eval(f"Notepad_{devType}()");
        if dev is not None:
            return dev

