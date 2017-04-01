import tkinter.ttk


class Style(tkinter.ttk.Style):
    def __init__(self, master, font_size=16):
        super().__init__(master)
        # self.configure('.', font=('Helvetica', font_size))
        # self.configure('Threads.Treeview', font=('Helvetica', font_size), background='white')
        self.configure('Treeview', font=('Helvetica', font_size))
        self.configure('Treeview.Heading', font=('Helvetica', font_size))
        # self.configure('Folders.Treeview', font=('Helvetica', font_size))
        self.configure('Message.Text', font=('Courier', font_size))
