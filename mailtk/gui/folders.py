import tkinter.ttk
from mailtk.gui.mixin import WidgetMixin


class Folders(tkinter.ttk.Treeview, WidgetMixin):
    def __init__(self, parent):
        super().__init__(parent, style='Folders.Treeview')
        self.heading('#0', text='Name')
        self.bind_async('<<TreeviewSelect>>', self.treeview_select)
        self.bind_async('<<TreeviewOpen>>', self.treeview_open)
        self.bind_async('<<TreeviewClose>>', self.treeview_close)

    async def treeview_select(self, ev):
        current = self.focus()
        try:
            account, o = self._folder_map[current]
        except KeyError:
            # Clicked something else
            return
        data = self.item(current)
        self.controller.set_selected_folder(account, o)

    async def treeview_open(self, ev):
        pass

    async def treeview_close(self, ev):
        pass

    def set_accounts(self, account_names):
        self._account_map = {}
        self._folder_map = {}
        self.set_children('')
        for n in account_names:
            v = self.insert('', tkinter.END, text=n)
            self._account_map[n] = v
            self.insert(v, 0, text='')

    def set_folders(self, account_name, folders):
        account = self._account_map[account_name]
        self.set_children(account)
        for o in folders:
            v = self.insert(account, tkinter.END, text=o.name)
            self._folder_map[v] = (account, o)
        self.item(account, open=True)
