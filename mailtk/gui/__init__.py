import asyncio
import tkinter
import tkinter.ttk


class Folders(tkinter.ttk.Treeview):
    def __init__(self, parent):
        super().__init__(parent)
        self.loop = parent.loop
        self.heading('#0', text='Name')
        self.bind('<Button-1>', self.event_cb(self.button1))

    def event_cb(self, method):
        return lambda ev: asyncio.ensure_future(method(ev), loop=self.loop)

    async def button1(self, ev):
        current = self.focus()
        self.master.message.set_value(repr(self.item(current)))

    def set_folders(self, folders):
        self.set_children('')
        for f in folders:
            v = self.insert('', tkinter.END, text=f)
            self.insert(v, 0, text='Test')


class Threads(tkinter.ttk.Treeview):
    def __init__(self, parent):
        super().__init__(parent, columns=('one', 'two'))
        self.loop = parent.loop
        self.heading('#0', text='zero')
        self.heading('one', text='One')
        self.heading('two', text='Two')
        self.insert('', 0, text='Line 1', values=('1', '2'))
        self.insert('', tkinter.END, text='Line 2', values=('1', '2'))
        print(self.get_children())


class Message(tkinter.Text):
    def __init__(self, parent):
        super().__init__(parent, state=tkinter.DISABLED)
        self.loop = parent.loop

    def set_value(self, text):
        self.configure(state=tkinter.NORMAL)
        self.delete(1.0, tkinter.END)
        self.insert(tkinter.END, text)
        self.configure(state=tkinter.DISABLED)


class MailGui(tkinter.Tk):
    def __init__(self, loop):
        super().__init__()
        self.loop = loop
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
