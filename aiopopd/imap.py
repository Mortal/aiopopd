import asyncio
from aiopopd.imap_backend import ImapBackend
from aiopopd.pop import log


class Message:
    def __init__(self, uid, deleted, size):
        self.uid = uid
        self.deleted = deleted
        self.size = size


SEEN = br'\Seen'


class ImapHandler:
    def __init__(self, *, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.backend = None

    async def get_backend(self, username, password):
        raise NotImplementedError

    def connection_lost(self):
        if self.backend:
            self.backend.connection_lost()

    async def handle_PASS(self, server, username, password):
        try:
            self.backend = await self.get_backend(username, password)
        except Exception as exn:
            log.exception('%s %s Exception in get_backend',
                          server.peer_str, username)
            server.username = None
            return '-ERR %s' % exn
        server.password = password
        server.state = 'TRANSACTION'
        self.messages = await self.list_messages()
        log.info('%s %r %s messages', server.peer_str, username,
                 len(self.messages))
        self.to_delete = []
        return '+OK remote login successful'

    async def list_messages(self):
        n_messages = await self.backend.select_folder('INBOX')
        if n_messages == 0:
            log.warning('%s %r SELECT returned 0 meaning no messages in inbox',
                        server.peer_str, username)
            return []
        message_ids = await self.backend.search()
        params = [
            'FLAGS', 'RFC822.SIZE',
            # 'BODY.PEEK[HEADER.FIELDS (Date From To Cc Subject ' +
            # 'Message-ID References In-Reply-To)]',
        ]
        data = await self.backend.fetch(message_ids, params)

        def is_deleted(imap_flags):
            return SEEN in imap_flags

        def parse(message_key, message_value):
            message_value.pop(b'SEQ', None)
            deleted = is_deleted(message_value.pop(b'FLAGS'))
            size = message_value.pop(b'RFC822.SIZE')
            return Message(message_key, deleted, size)

        all_messages = (parse(k, v) for k, v in data.items())
        return [m for m in all_messages if not m.deleted]

    async def handle_QUIT(self, server):
        if server.state == 'TRANSACTION':
            to_delete = [m.uid for m in self.messages if m.deleted]
            if to_delete:
                log.info('%s %s Delete %s message(s)',
                         server.peer_str, server.username, len(to_delete))
                await self.backend.add_flags(to_delete, [SEEN])
        if self.backend is not None:
            await self.backend.disconnect()
            self.backend = None
        return '+OK Bye'

    async def handle_STAT(self, server):
        n = sum(1 for m in self.messages if not m.deleted)
        size = sum(m.size for m in self.messages if not m.deleted)
        return '+OK %s %s' % (n, size)

    async def handle_LIST(self, server, n):
        m = self.messages[n-1]
        if not m.deleted:
            return m.size

    async def handle_UIDL(self, server, n):
        m = self.messages[n-1]
        if not m.deleted:
            return m.uid

    async def handle_RETR(self, server, n):
        m = self.messages[n-1]
        if m.deleted:
            return '-ERR message deleted'
        params = ['RFC822']
        data, = (await self.backend.fetch([m.uid], params)).values()
        await server.push_multi('+OK message follows', data[b'RFC822'])

    async def handle_DELE(self, server, n):
        m = self.messages[n-1]
        if m.deleted:
            return '-ERR message already deleted'
        m.deleted = True
        return '+OK deleted'

    async def handle_RSET(self, server):
        for m in self.messages:
            m.deleted = False
        return '+OK'


class ImapHandlerFixed(ImapHandler):
    def __init__(self, hostname, port, ssl, **kwargs):
        super().__init__(**kwargs)
        self.hostname = hostname
        self.port = port
        self.ssl = ssl

    async def get_backend(self, username, password):
        backend = ImapBackend(loop=self.loop, host=self.hostname,
                              port=self.port, ssl=self.ssl)
        await backend.connect()
        await backend.login(username, password)
        return backend
