import traceback
import tkinter
import tkinter.ttk

from mailtk.gui.folders import Folders
from mailtk.gui.threads import Threads
from mailtk.gui.message import Message
from mailtk.gui.style import Style


class MailGui(tkinter.Tk):
    def __init__(self, loop):
        super().__init__()
        self.style = Style(self)
        self.loop = loop
        self.controller = None
        self.title('MailTk')
        self.hpane = tkinter.ttk.Panedwindow(self, orient='horizontal')
        self.hpane.grid(row=0, column=0)
        self.rowconfigure(0, weight=1)
        self.folders = Folders(self)
        self.vpane = tkinter.ttk.Panedwindow(self, orient='vertical')
        # self.vpane.pack(fill='both', expand=True)
        self.threads = Threads(self)
        self.message = Message(self)
        self.hpane.add(self.folders, weight=1)
        self.vpane.add(self.threads, weight=1)
        self.vpane.add(self.message, weight=1)
        self.hpane.add(self.vpane, weight=1)
        self.statusbar = tkinter.ttk.Label(
            self, borderwidth=1, relief=tkinter.SUNKEN, anchor='w')
        self.statusbar.grid(row=1, column=0, sticky='news')

    def set_status(self, text):
        self.statusbar.configure(text=text)

    def selected_folder(self):
        return self.folders.selected_folder()

    def set_accounts(self, account_names):
        self.folders.set_accounts(account_names)

    def set_folders(self, account, mailboxes):
        self.folders.set_folders(account, mailboxes)

    def set_threads(self, threads):
        self.threads.set_threads(threads, 0, len(threads))

    def handle_exception(self):
        self.message.set_value(traceback.format_exc())

    def log_debug(self, msg):
        self.message.set_value(msg)

    def set_message(self, message: bytes):
        self.message.set_message(message)
