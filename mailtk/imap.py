import os
import re
import queue
import asyncio
import imaplib
import threading


class ImapAccount:
    def __init__(self, loop, host, port, ssl):
        self.backend = ImapBackend(loop, host, port, ssl)

    async def __aenter__(self):
        await self.backend.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return await self.backend.__aexit__(exc_type, exc, tb)

    @property
    def capabilities(self):
        return self.backend.capabilities

    async def login(self, user, password):
        return await self.backend.login(user, password)

    def _check_code(self, result):
        code, data = result
        if code != 'OK':
            assert len(data) == 1
            raise Exception(data[0].decode())
        return data

    def parse_mailbox(self, response):
        mo = re.match(r'^\((?P<a>[^)]+)\) (?P<sep>NIL|"[^"]*") ' +
                      r'(?P<name>.*)$', response.decode())
        if not mo:
            raise ValueError(response.decode())
        return mo.group('name')

    async def list(self):
        response = self._check_code(await self.backend.list())
        mailboxes = [self.parse_mailbox(r) for r in response]
        return mailboxes


class ImapBackend:
    BREAK = object()
    READY = object()

    def __init__(self, loop, host, port, ssl):
        self._loop = loop
        self._host = host
        self._port = port
        self._ssl = ssl
        self._command_queue = queue.Queue()
        self._response_queue = queue.Queue()
        self._ready_r, self._ready_w = os.pipe()
        loop.add_reader(self._ready_r, self._ready)
        self._ready = threading.Event()
        self._thread = threading.Thread(None, self._run)
        self._breaking = False

    async def __aenter__(self):
        self._thread.start()
        self.capabilities = await self._call(self.READY)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._call(self.BREAK)
        self._thread.join()

    async def _call(self, method, *args):
        if self._breaking:
            raise Exception('connection is closing')
        future = asyncio.Future(loop=self._loop)
        self._command_queue.put_nowait((future, method, args))
        if method is self.BREAK:
            self._breaking = True
        return await future

    def _run(self):
        # Run commands in thread
        class_ = imaplib.IMAP4_SSL if self._ssl else imaplib.IMAP4
        with class_(self._host, self._port) as conn:
            while True:
                future, method, args = self._command_queue.get()
                if method is self.BREAK:
                    break
                elif method is self.READY:
                    result = conn.capabilities
                else:
                    # TODO check if future is cancelled
                    try:
                        result = getattr(conn, method)(*args)
                    except Exception as exn:
                        result = exn
                self._response_queue.put((future, result))
                self._command_queue.task_done()
                os.write(self._ready_w, b'x')

        assert method is self.BREAK
        self._response_queue.put((future, None))
        self._command_queue.task_done()
        os.write(self._ready_w, b'x')

    def _ready(self):
        os.read(self._ready_r, 1)
        future, result = self._response_queue.get_nowait()
        future.set_result(result)
        self._response_queue.task_done()

    # The following methods were generated by gen-imap.py
    async def append(self, mailbox, flags, date_time, message):
        'Append message to named mailbox.'
        return await self._call('append', mailbox, flags, date_time, message)

    async def authenticate(self, mechanism, authobject):
        'Authenticate command - requires response processing.'
        return await self._call('authenticate', mechanism, authobject)

    async def capability(self):
        '(typ, [data]) = <instance>.'
        return await self._call('capability')

    async def check(self):
        'Checkpoint mailbox on server.'
        return await self._call('check')

    async def close(self):
        'Close currently selected mailbox.'
        return await self._call('close')

    async def copy(self, message_set, new_mailbox):
        "Copy 'message_set' messages onto end of 'new_mailbox'."
        return await self._call('copy', message_set, new_mailbox)

    async def create(self, mailbox):
        'Create new mailbox.'
        return await self._call('create', mailbox)

    async def delete(self, mailbox):
        'Delete old mailbox.'
        return await self._call('delete', mailbox)

    async def deleteacl(self, mailbox, who):
        'Delete the ACLs (remove any rights) set for who on mailbox.'
        return await self._call('deleteacl', mailbox, who)

    async def enable(self, capability):
        'Send an RFC5161 enable string to the server.'
        return await self._call('enable', capability)

    async def expunge(self):
        'Permanently remove deleted items from selected mailbox.'
        return await self._call('expunge')

    async def fetch(self, message_set, message_parts):
        'Fetch (parts of) messages.'
        return await self._call('fetch', message_set, message_parts)

    async def getacl(self, mailbox):
        'Get the ACLs for a mailbox.'
        return await self._call('getacl', mailbox)

    async def getannotation(self, mailbox, entry, attribute):
        '(typ, [data]) = <instance>.'
        return await self._call('getannotation', mailbox, entry, attribute)

    async def getquota(self, root):
        "Get the quota root's resource usage and limits."
        return await self._call('getquota', root)

    async def getquotaroot(self, mailbox):
        'Get the list of quota roots for the named mailbox.'
        return await self._call('getquotaroot', mailbox)

    async def list(self, directory='""', pattern='*'):
        'List mailbox names in directory matching pattern.'
        return await self._call('list', directory, pattern)

    async def login(self, user, password):
        'Identify client using plaintext password.'
        return await self._call('login', user, password)

    async def login_cram_md5(self, user, password):
        ' Force use of CRAM-MD5 authentication.'
        return await self._call('login_cram_md5', user, password)

    async def logout(self):
        'Shutdown connection to server.'
        return await self._call('logout')

    async def lsub(self, directory='""', pattern='*'):
        "List 'subscribed' mailbox names in directory matching pattern."
        return await self._call('lsub', directory, pattern)

    async def myrights(self, mailbox):
        'Show my ACLs for a mailbox (i.'
        return await self._call('myrights', mailbox)

    async def namespace(self):
        ' Returns IMAP namespaces ala rfc2342'
        return await self._call('namespace')

    async def noop(self):
        'Send NOOP command.'
        return await self._call('noop')

    async def open(self, host='', port=143):
        'Setup connection to remote server on "host:port"'
        return await self._call('open', host, port)

    async def partial(self, message_num, message_part, start, length):
        'Fetch truncated part of a message.'
        return await self._call(
            'partial', message_num, message_part, start, length)

    async def print_log(self):
        return await self._call('print_log')

    async def proxyauth(self, user):
        'Assume authentication as "user".'
        return await self._call('proxyauth', user)

    async def read(self, size):
        "Read 'size' bytes from remote."
        return await self._call('read', size)

    async def readline(self):
        'Read line from remote.'
        return await self._call('readline')

    async def recent(self):
        "Return most recent 'RECENT' responses if any exist,"
        return await self._call('recent')

    async def rename(self, oldmailbox, newmailbox):
        'Rename old mailbox name to new.'
        return await self._call('rename', oldmailbox, newmailbox)

    async def response(self, code):
        "Return data for response 'code' if received, or None."
        return await self._call('response', code)

    async def search(self, charset, *criteria):
        'Search mailbox for matching messages.'
        return await self._call('search', charset, *criteria)

    async def select(self, mailbox='INBOX', readonly=False):
        'Select a mailbox.'
        return await self._call('select', mailbox, readonly)

    async def send(self, data):
        'Send data to remote.'
        return await self._call('send', data)

    async def setacl(self, mailbox, who, what):
        'Set a mailbox acl.'
        return await self._call('setacl', mailbox, who, what)

    async def setannotation(self, *args):
        '(typ, [data]) = <instance>.'
        return await self._call('setannotation', *args)

    async def setquota(self, root, limits):
        "Set the quota root's resource limits."
        return await self._call('setquota', root, limits)

    async def shutdown(self):
        'Close I/O established in "open".'
        return await self._call('shutdown')

    async def socket(self):
        'Return socket instance used to connect to IMAP4 server.'
        return await self._call('socket')

    async def sort(self, sort_criteria, charset, *search_criteria):
        'IMAP4rev1 extension SORT command.'
        return await self._call(
            'sort', sort_criteria, charset, *search_criteria)

    async def starttls(self, ssl_context=None):
        return await self._call('starttls', ssl_context)

    async def status(self, mailbox, names):
        'Request named status conditions for mailbox.'
        return await self._call('status', mailbox, names)

    async def store(self, message_set, command, flags):
        'Alters flag dispositions for messages in mailbox.'
        return await self._call('store', message_set, command, flags)

    async def subscribe(self, mailbox):
        'Subscribe to new mailbox.'
        return await self._call('subscribe', mailbox)

    async def thread(self, threading_algorithm, charset, *search_criteria):
        'IMAPrev1 extension THREAD command.'
        return await self._call(
            'thread', threading_algorithm, charset, *search_criteria)

    async def uid(self, command, *args):
        'Execute "command arg .'
        return await self._call('uid', command, *args)

    async def unsubscribe(self, mailbox):
        'Unsubscribe from old mailbox.'
        return await self._call('unsubscribe', mailbox)

    async def xatom(self, name, *args):
        'Allow simple extension commands'
        return await self._call('xatom', name, *args)
    # End generated methods
