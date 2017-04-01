import tkinter.ttk
from aiotkinter import WidgetMixin


class Message(tkinter.Text, WidgetMixin):
    def __init__(self, parent):
        super().__init__(parent, state=tkinter.DISABLED)

    def set_value(self, text):
        self.configure(state=tkinter.NORMAL)
        self.delete(1.0, tkinter.END)
        self.insert(tkinter.END, text)
        self.configure(state=tkinter.DISABLED)

    def handle_exception(self):
        raise
