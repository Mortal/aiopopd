from aiopopd.imap_backend import ImapBackend


class ImapHandler:
    def __init__(self, hostname, port, ssl, *, loop=None):
        self.hostname = hostname
        self.port = port
        self.ssl = ssl
        self.loop = loop or asyncio.get_event_loop()

    async def handle_PASS(self, server, username, password):
        try:
            self.backend = ImapBackend(loop=self.loop, host=self.hostname,
                                       port=self.port, ssl=self.ssl)
            await self.backend.connect()
            await self.backend.login(username, password)
        except Exception as exn:
            server.username = None
            return '-ERR %s' % exn
        server.password = password
        self.messages = await self.list_messages()
        self.to_delete = []
        return '+OK remote login successful'

    async def list_messages(self):
        n_messages = await self.backend.select_folder('INBOX')
        if n_messages == 0:
            return []
        message_ids = await self.backend.search()
        params = [
            'FLAGS', 'RFC822.SIZE',
            # 'BODY.PEEK[HEADER.FIELDS (Date From To Cc Subject ' +
            # 'Message-ID References In-Reply-To)]',
        ]
        data = await self.backend.fetch(message_ids, params)

        def is_deleted(imap_flags):
            return b'\\Seen' in imap_flags

        def parse(message_key, message_value):
            message_value.pop(b'SEQ', None)
            deleted = is_deleted(message_value.pop(b'FLAGS'))
            size = message_value.pop(b'RFC822.SIZE')

            message_id = header('Message-ID')
            date_header = header('Date')
            return message_id, ThreadMessage(
                flag=flag,
                size=size,
                date=email.utils.parsedate_to_datetime(
                    date_header) if date_header is not None else None,
                from_=header('From'),
                to=header('To'),
                cc=header('Cc'),
                subject=header('Subject'),
                message_id=message_id,
                references=header('References', '').split(),
                in_reply_to=header('In-Reply-To', '').split(),
                key=message_key,
                children=[],
            )

        messages = dict(parse(k, v) for k, v in data.items())
        toplevel = []
        for m in messages.values():
            for p in m.in_reply_to + m.references:
                try:
                    messages[p].children.append(m)
                    break
                except KeyError:
                    pass
            else:
                toplevel.append(m)

        def thread_date(m):
            return max([(m.date is not None, m.date and m.date.tzinfo is None, m.date)] +
                       [thread_date(c) for c in m.children])

        toplevel.sort(key=thread_date, reverse=True)

        def convert(o: ThreadMessage):
            v = ThreadInfo(
                flag=o.flag,
                size=o.size,
                date=o.date,
                sender=o.from_,
                recipients=', '.join(filter(None, (o.to, o.cc))),
                subject=o.subject,
                children=[convert(c) for c in o.children],
                excerpt='',
            )
            return ThreadInfoImap(v, mailbox, o.key)

        return [convert(t) for t in toplevel]

    async def handle_QUIT(self, server):
        if server.state == 'TRANSACTION':
