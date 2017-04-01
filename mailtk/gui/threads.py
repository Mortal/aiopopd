import tkinter.ttk
from aiotkinter import WidgetMixin


class Threads(tkinter.ttk.Treeview, WidgetMixin):
    thread_columns = ('recipients', 'subject', 'date', 'excerpt')

    def __init__(self, parent):
        super().__init__(parent, columns=self.thread_columns)
        self.heading('#0', text='#')
        for k in self.thread_columns:
            self.heading(k, text=k[0].upper() + k[1:])
        self.bind_async('<Button-1>', self.button1)
        self._thread_map = None

    async def button1(self, ev):
        current = self.focus()
        # data = self.item(current)
        o = self._thread_map[current]
        self.controller.set_selected_thread(o)

    def set_threads(self, threads, skip, total):
        self._thread_map = {}
        self.set_children('')
        dummy = tuple('-' for _ in self.thread_columns)
        for i in range(skip):
            self.insert('', tkinter.END, text='%s' % i, values=dummy)
        for i, o in enumerate(threads, skip):
            values = tuple(getattr(o, k) for k in self.thread_columns)
            v = self.insert('', tkinter.END, text='%s' % i, values=values)
            self._thread_map[v] = o
        for i in range(skip + len(threads), total):
            self.insert('', tkinter.END, text='%s' % i, values=dummy)
