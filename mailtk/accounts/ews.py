import os
import queue
import base64
import asyncio
import threading
import exchangelib
from mailtk.data import Mailbox, ThreadInfo, Flag
from mailtk.accounts.base import AccountBase


class MailboxExchange(Mailbox):
    _fields = 'folder'

class ThreadInfoExchange(ThreadInfo):
    _fields = 'folder message_id'


class ExchangeAccount(AccountBase):
    @classmethod
    async def initialize(cls, loop, host, username, password, email):
        account = cls(loop, host, username, password, email)
        await account.connect()
        return account

    BREAK = object()
    NOOP = object()

    def __init__(self, loop, host, username, password, email):
        self._loop = loop
        self._host = host
        self._email = email
        self._credentials = exchangelib.Credentials(
            username=username,
            password=password,
        )
        self._command_queue = queue.Queue()
        self._response_queue = queue.Queue()
        self._ready_r, self._ready_w = os.pipe()
        loop.add_reader(self._ready_r, self._ready)
        self._thread = threading.Thread(None, self._run)
        self._breaking = False

    async def connect(self):
        self._thread.start()
        await self._call(self.NOOP)

    async def disconnect(self):
        await self._call(self.BREAK)
        self._thread.join()

    async def _call(self, method, *args):
        if self._breaking:
            raise Exception('connection is closing')
        future = asyncio.Future(loop=self._loop)
        self._command_queue.put_nowait((future, method, args))
        if method is self.BREAK:
            self._breaking = True
        result = await future
        if isinstance(result, Exception):
            raise result
        return result

    def rpc(method):
        async def wrapper(self, *args):
            return await self._call(method, *args)

        return wrapper

    @rpc
    def list_folders(self, account):
        top = account.root.get_folder_by_name('Top of Information Store')

        def make_mailbox(f):
            children = (f.get_folders(depth=exchangelib.SHALLOW)
                        if f.child_folder_count else ())
            child_mailboxes = [make_mailbox(c) for c in children
                               if isinstance(c, exchangelib.folders.Messages)]
            return MailboxExchange(
                Mailbox(f.name, child_mailboxes), f)

        folders = top.get_folders(depth=exchangelib.SHALLOW)
        return [make_mailbox(c) for c in folders
                if isinstance(c, exchangelib.folders.Messages)]

    @rpc
    def list_messages(self, account, folder: MailboxExchange):
        f = folder.folder  # type: exchangelib.folders.Messages
        messages = []
        qs = f.all()
        qs = qs.values('message_id', 'datetime_received', 'sender', 'subject')
        qs = qs[:20]
        for o in qs:
            try:
                message_id = o.pop('message_id')
                dt = o.pop('datetime_received')
                sender = o.pop('sender')
                subject = o.pop('subject')
            except KeyError:
                raise Exception(o)
            thread_info = ThreadInfo(
                flag=Flag.read, size=42, date=dt,
                subject=subject, sender=sender,
                recipients=[],
                children=[], excerpt='foo')
            messages.append(ThreadInfoExchange(thread_info, folder, message_id))
        return messages

    @rpc
    def fetch_message(self, account, threadinfo: ThreadInfoExchange):
        folder = threadinfo.folder
        message_id = threadinfo.message_id
        qs = folder.folder.filter(message_id=message_id)
        o, = qs
        return base64.b64decode(o.mime_content)

    del rpc

    def _run(self):
        # Run commands in thread
        try:
            if self._host == 'auto':
                account = exchangelib.Account(
                    primary_smtp_address=self._email,
                    credentials=self._credentials,
                    autodiscover=True, access_type=exchangelib.DELEGATE)
            else:
                config = exchangelib.Configuration(
                    server=self._host,
                    credentials=self._credentials,
                    auth_type=exchangelib.NTLM,
                )
                account = exchangelib.Account(
                    primary_smtp_address=self._email, config=config,
                    access_type=exchangelib.DELEGATE)
        except Exception as exn:
            future, method, args = self._command_queue.get()
            self._response_queue.put((future, exn))
            self._command_queue.task_done()
            os.write(self._ready_w, b'x')
            return
        try:
            while True:
                future, method, args = self._command_queue.get()
                if method is self.BREAK:
                    break
                elif method is self.NOOP:
                    result = None
                else:
                    # TODO check if future is cancelled
                    try:
                        result = method(self, account, *args)
                    except Exception as exn:
                        result = exn
                self._response_queue.put((future, result))
                self._command_queue.task_done()
                os.write(self._ready_w, b'x')
        finally:
            del account
            del config

        assert method is self.BREAK
        self._response_queue.put((future, None))
        self._command_queue.task_done()
        os.write(self._ready_w, b'x')

    def _ready(self):
        os.read(self._ready_r, 1)
        future, result = self._response_queue.get_nowait()
        if not future.cancelled():
            future.set_result(result)
        self._response_queue.task_done()
