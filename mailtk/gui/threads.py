import tkinter.ttk
from mailtk.gui.autoscrollbar import AutoScrollbar
from mailtk.gui.mixin import WidgetMixin


class Threads(tkinter.ttk.Frame, WidgetMixin):
    thread_columns = ('sender', 'flag', 'size', 'date', 'excerpt')

    def __init__(self, parent):
        super().__init__(parent)
        self.scrollbar = AutoScrollbar(self, orient=tkinter.VERTICAL)
        self.tv = tkinter.ttk.Treeview(self, columns=self.thread_columns,
                                       style='Threads.Treeview',
                                       yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.tv.yview)
        self.tv.heading('#0', text='Subject')
        for k in self.thread_columns:
            self.tv.heading(k, text=k[0].upper() + k[1:])
        self.bind_async(self.tv, '<<TreeviewSelect>>', self.treeview_select)
        self.bind_async(self.tv, '<<TreeviewOpen>>', self.treeview_open)
        self.bind_async(self.tv, '<<TreeviewClose>>', self.treeview_close)

        self.tv.grid(row=0, column=0, sticky='news')
        self.scrollbar.grid(row=0, column=1, sticky='ns')
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._thread_map = None

    async def treeview_select(self, ev):
        current = self.tv.focus()
        # data = self.tv.item(current)
        o = self._thread_map[current]
        self.controller.set_selected_thread(o)

    async def treeview_open(self, ev):
        pass

    async def treeview_close(self, ev):
        pass

    def _insert_children(self, threads, parent):
        for o in threads:
            values = tuple(getattr(o, k) or '' for k in self.thread_columns)
            v = self.tv.insert(parent, tkinter.END, text=o.subject or '',
                               values=values)
            self._thread_map[v] = o
            self._insert_children(o.children, v)
            if o.children:
                self.tv.item(v, open=True)

    def set_threads(self, threads, skip, total):
        self._thread_map = {}
        self.tv.set_children('')
        dummy = tuple('-' for _ in self.thread_columns)
        for i in range(skip):
            self.tv.insert('', tkinter.END, text='%s' % i, values=dummy)
        self._insert_children(threads, '')
        for i in range(skip + len(threads), total):
            self.tv.insert('', tkinter.END, text='%s' % i, values=dummy)
