'''
From http://effbot.org/zone/tkinter-autoscrollbar.htm
'''

import tkinter
import tkinter.ttk


class AutoScrollbar(tkinter.ttk.Scrollbar):
    '''
    A scrollbar that hides itself if it's not needed.
    Only works if you use the grid geometry manager.
    '''

    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
        super().set(lo, hi)

    def pack(self, **kw):
        raise tkinter.TclError("cannot use pack with this widget")

    def place(self, **kw):
        raise tkinter.TclError("cannot use place with this widget")
