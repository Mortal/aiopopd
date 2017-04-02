import asyncio
from mailtk.data import Mailbox, ThreadInfo
import traceback
import pprint
import contextlib
import functools


class ThreadAccount(ThreadInfo):
    _fields = 'account'

    @property
    def children(self):
        return [ThreadAccount(c, self.account)
                for c in self.inner_threadinfo.children]


class MailboxAccount(Mailbox):
    _fields = 'account account_name'

    @property
    def children(self):
        return [MailboxAccount(c, self.account, self.account_name)
                for c in self.inner_mailbox.children]


class Controller:
    def __init__(self, loop, accounts, gui):
        self.loop = loop
        self.accounts = accounts
        self.gui = gui
        self.gui.controller = self
        self.statuses = []
        self.init_accounts_result = self.ensure_future(self.init_accounts())
        self.pending_interaction = None

    @contextlib.contextmanager
    def set_status(self, text):
        contextlib.ContextDecorator
        self.statuses.append(text)
        self.gui.set_status(' '.join(self.statuses))
        try:
            yield
        finally:
            self.statuses.remove(text)
            self.gui.set_status(' '.join(self.statuses))

    def status(text):
        def decorator(method):
            @functools.wraps(method)
            async def wrapper(self, *args, **kwargs):
                with self.set_status(text):
                    return await method(self, *args, **kwargs)

            return wrapper

        return decorator

    def ensure_future(self, coro):
        async def wrapper():
            try:
                return await coro
            except Exception:
                self.handle_exception()

        return asyncio.ensure_future(wrapper(), loop=self.loop)

    @status('Initializing accounts...')
    async def init_accounts(self):
        self.gui.set_accounts(self.accounts.keys())
        account_coros = []
        for k, v in self.accounts.items():
            account_coros.append(self.init_account(k, v))
        await asyncio.gather(*account_coros, loop=self.loop,
                             return_exceptions=True)
        self.log_debug('Finished initializing accounts')

    async def init_account(self, account_name, get_account):
        try:
            with self.set_status('Login %s...' % account_name):
                account = await get_account(self)
        except Exception:
            self.log_exception("Failed to connect to %r" %
                               (account_name,))
            return
        try:
            with self.set_status('List %s...' % account_name):
                mailboxes = await account.list_folders()
            assert all(isinstance(f, Mailbox) for f in mailboxes)
            folders = [MailboxAccount(f, account, account_name)
                       for f in mailboxes]
            self.gui.set_folders(account_name, folders)
            self.folders = folders
        except Exception:
            self.log_exception('Failed to initialize account %r' %
                               (account_name,))

    def handle_exception(self):
        self.log_exception('Unhandled exception caught by mailtk.Controller')

    def log_exception(self, msg):
        s = traceback.format_exc()
        if msg:
            s = '\n\n'.join((msg, traceback.format_exc()))
        print(s)
        self.log_debug(s)

    def log_debug(self, msg):
        self.gui.log_debug(msg)

    def set_interaction(self, coro):
        if self.pending_interaction and not self.pending_interaction.done():
            self.pending_interaction.cancel()
        self.pending_interaction = self.ensure_future(coro)

    def set_selected_folder(self, folder):
        self.log_debug("Selected folder: %r" % (folder,))
        self.set_interaction(self._set_selected_folder(folder))

    async def _set_selected_folder(self, folder):
        mailbox = folder.inner_mailbox
        with self.set_status('Opening %s in %s...' %
                             (mailbox.name, folder.account_name)):
            try:
                result = await folder.account.list_messages(mailbox)
            except asyncio.CancelledError:
                print("Cancelled set_selected_folder")
                return
        result = [ThreadAccount(thread, folder.account)
                  for thread in result]
        self.gui.set_threads(result)
        self.gui.set_message(None)
        self.log_debug("Selected folder: %r" % (folder,))

    def set_selected_thread(self, thread):
        self.set_interaction(self._set_selected_thread(thread))

    async def _set_selected_thread(self, thread):
        self.log_debug(repr(thread))
        with self.set_status('Fetching %r...' % (thread.subject,)):
            try:
                message = await thread.account.fetch_message(
                    thread.inner_threadinfo)
            except asyncio.CancelledError:
                print("Cancelled set_selected_thread")
                return
        self.gui.set_message(message)
        # TODO: Set flag to Flag.read

    del status
