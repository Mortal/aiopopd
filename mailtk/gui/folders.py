import tkinter.ttk
from aiotkinter import WidgetMixin


class Folders(tkinter.ttk.Treeview, WidgetMixin):
    def __init__(self, parent):
        super().__init__(parent)
        self.heading('#0', text='Name')
        self.bind_async('<Button-1>', self.button1)

    async def button1(self, ev):
        current = self.focus()
        if not current:
            return
        # data = self.item(current)
        o = self._folder_map[current]
        self.controller.set_selected_folder(o)

    def set_folders(self, folders):
        self._folder_map = {}
        self.set_children('')
        for o in folders:
            v = self.insert('', tkinter.END, text=o.name)
            self._folder_map[v] = o
            self.insert(v, 0, text='Test')
