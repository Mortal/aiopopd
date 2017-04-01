import asyncio
from mailtk.data import Mailbox, MailboxAccount, ThreadAccount
import traceback
import pprint


class Controller:
    def __init__(self, loop, accounts, gui):
        self.loop = loop
        self.accounts = accounts
        self.gui = gui
        self.gui.controller = self
        self.ensure_future(self.init_accounts())
        self.pending_interaction = None

    def ensure_future(self, coro):
        async def wrapper():
            try:
                return await coro
            except Exception:
                self.handle_exception()

        return asyncio.ensure_future(wrapper(), loop=self.loop)

    async def init_accounts(self):
        self.gui.set_accounts(self.accounts.keys())
        for k, v in self.accounts.items():
            self.ensure_future(self.init_account(k, v))

    async def init_account(self, account_name, get_account):
        account = await get_account(self)
        mailboxes = await account.list_folders()
        self.log_debug(repr(mailboxes))
        assert all(isinstance(f, Mailbox) for f in mailboxes)
        folders = [MailboxAccount(f, account) for f in mailboxes]
        self.gui.set_folders(account_name, folders)
        self.folders = folders

    def handle_exception(self):
        self.log_debug(traceback.format_exc())

    def log_debug(self, msg):
        self.gui.log_debug(msg)

    def set_interaction(self, coro):
        if self.pending_interaction and not self.pending_interaction.done():
            self.pending_interaction.cancel()
        self.pending_interaction = self.ensure_future(coro)

    def set_selected_folder(self, account, folder):
        self.set_interaction(self._set_selected_folder(account, folder))

    async def _set_selected_folder(self, account_name, folder):
        mailbox, account = folder
        result = await account.list_messages(mailbox)
        result = [ThreadAccount(inner, account, handle)
                  for inner, handle in result]
        self.gui.set_threads(result)
        self.gui.set_message(None)

    def set_selected_thread(self, thread):
        self.set_interaction(self._set_selected_thread(thread))

    async def _set_selected_thread(self, thread):
        self.log_debug(repr(thread))
        self.log_debug('Fetching %r...' % (thread.subject,))
        message = await thread.account.fetch_message(thread.handle)
        self.gui.set_message(message)
        # mailbox, account = folder
        # result = await account.list_messages(mailbox)
        # self.gui.set_threads(result)
