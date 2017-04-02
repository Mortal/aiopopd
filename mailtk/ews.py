import exchangelib
import queue
import os
import asyncio
from mailtk.data import Mailbox
import threading
import exchangelib


class ExchangeAccount:
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
        self._ready = threading.Event()
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
            return Mailbox(f.name, child_mailboxes)

        folders = top.get_folders(depth=exchangelib.SHALLOW)
        return [make_mailbox(c) for c in folders
                if isinstance(c, exchangelib.folders.Messages)]

    del rpc

    def _run(self):
        # Run commands in thread
        try:
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
