import traceback
import tkinter
import tkinter.ttk
from aiotkinter import WidgetMixin
from mailtk.data import ThreadInfo


class Folders(tkinter.ttk.Treeview, WidgetMixin):
    def __init__(self, parent):
        super().__init__(parent)
        self.heading('#0', text='Name')
        self.bind_async('<Button-1>', self.button1)

    async def button1(self, ev):
        current = self.focus()
        if not current:
            return
        data = self.item(current)
        o = self._folder_map[current]
        self.controller.set_selected_folder(o)

    def set_folders(self, folders):
        self._folder_map = {}
        self.set_children('')
        for o in folders:
            v = self.insert('', tkinter.END, text=repr(o.name))
            self._folder_map[v] = o
            self.insert(v, 0, text='Test')


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
        data = self.item(current)
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


class MailGui(tkinter.Tk):
    def __init__(self, loop):
        super().__init__()
        self.loop = loop
        self.controller = None
        self.title('MailTk')
        self.hpane = tkinter.ttk.Panedwindow(self, orient='horizontal')
        self.folders = Folders(self)
        self.vpane = tkinter.ttk.Panedwindow(self, orient='vertical')
        self.threads = Threads(self)
        self.message = Message(self)
        self.hpane.add(self.folders)
        self.vpane.add(self.threads)
        self.vpane.add(self.message)
        self.vpane.pack(fill='both', expand=True)
        self.hpane.add(self.vpane)
        self.hpane.pack(fill='both', expand=True)

    def selected_folder(self):
        return self.folders.selected_folder()

    def set_folders(self, mailboxes):
        self.folders.set_folders(mailboxes)

    def set_threads(self, threads):
        self.threads.set_threads(threads, 0, len(threads))

    def handle_exception(self):
        self.message.set_value(traceback.format_exc())

    def log_debug(self, msg):
        self.message.set_value(msg)

    def set_message(self, message: bytes):
        self.message.set_value(message.decode().replace('\r', ''))
