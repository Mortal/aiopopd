import tkinter.ttk
import tkinter


class Style(tkinter.ttk.Style):
    def __init__(self, master, font_size=16):
        super().__init__(master)
        # self.configure('.', font=('Helvetica', font_size))
        # self.configure('Threads.Treeview', font=('Helvetica', font_size), background='white')
        self.configure('Treeview', font=('Helvetica', font_size))
        self.configure('Treeview.Heading', font=('Helvetica', font_size))
        # self.configure('Folders.Treeview', font=('Helvetica', font_size))
        self.configure('Message.Text', font=('Courier', font_size))
        self.configure('Statusbar.TLabel', pady=3, border=1, relief=tkinter.SUNKEN,
                       font=('Helvetica', font_size))
