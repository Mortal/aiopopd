import traceback
import tkinter
import tkinter.ttk

from mailtk.gui.folders import Folders
from mailtk.gui.threads import Threads
from mailtk.gui.message import Message


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
        self.message.set_message(message)
