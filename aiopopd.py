import socket
import asyncio
import logging
import functools


def command(state):
    def decorator(fn):
        fn.command_state = state
        return fn

    return decorator


class POP(asyncio.StreamReaderProtocol):
    __ident__ = 'aiopopd'

    def __init__(self):
        self.hostname = socket.gethostname()
        self.loop = asyncio.get_event_loop()
        super().__init__(
            asyncio.StreamReader(loop=self.loop),
            client_connected_cb=self._client_connected_cb,
            loop=self.loop)

    def connection_made(self, transport):
        self.peer = transport.get_extra_info('peername')
        self.username = self.password = None
        super().connection_made(transport)
        self.transport = transport
        self._handler_coroutine = self.loop.create_task(
            self._handle_client())
        self.messages = []  # TODO

    def connection_lost(self, error):
        super().connection_lost(error)
        self._handler_coroutine.cancel()

    def eof_received(self):
        self._handler_coroutine.cancel()
        return super().eof_received()

    def _client_connected_cb(self, reader, writer):
        self._reader = reader
        self._writer = writer

    async def push(self, status):
        response = (status + '\r\n').encode('ascii')
        self._writer.write(response)
        log.debug(response)
        await self._writer.drain()

    async def handle_exception(self, error):
        TODO

    async def update(self):
        TODO

    async def _handle_client(self):
        try:
            self.state = 'AUTHORIZATION'
            log.info('%r handling connection', self.peer)
            await self.push('+OK {} {}'.format(self.hostname, self.__ident__))
            while self.transport is not None:
                line = await self._reader.readline()
                log.debug('_handle_client readline: %s', line)
                line = line.rstrip(b'\r\n')
                log.info('%r Data: %s', self.peer, line)
                if not line:
                    await self.push('500 Error: bad syntax')
                    continue
                line = line.decode('ascii')
                try:
                    command, arg = line.split(' ', 1)
                except ValueError:
                    command, arg = line, None
                method = getattr(self, 'pop3_' + command, None)
                method_state = getattr(method, 'command_state', None)
                if method_state is not None and method_state != self.state:
                    await self.push(
                        '-ERR wrong state for "%s"' % command)
                    continue
                if method is None:
                    await self.push(
                        '-ERR command "%s" not recognized' % command)
                    continue
                await method(arg)
        except Exception:
            log.exception("Unhandled exception in _handle_client")
            raise

    @command('AUTHORIZATION')
    async def pop3_USER(self, arg):
        if self.username is not None:
            await self.push('-ERR already supplied username')
            return
        self.username = arg
        await self.push('+OK name is a valid mailbox')

    @command('AUTHORIZATION')
    async def pop3_PASS(self, arg):
        if self.username is None:
            await self.push('-ERR must supply username first')
            return
        self.password = arg
        self.state = 'TRANSACTION'
        n = 2
        m = 320
        await self.push('+OK maildrop has %s messages (%s octets)' % (n, m))

    @command('AUTHORIZATION')
    async def pop3_APOP(self, arg):
        await self.push('-ERR APOP not implemented')

    async def pop3_QUIT(self, arg):
        if self.state == 'TRANSACTION':
            await self.update()
        await self.push('+OK Bye')
        self._handler_coroutine.cancel()
        self.transport.close()

    @command('TRANSACTION')
    async def pop3_STAT(self, arg):
        n = len(self.messages)  # number of messages in maildrop
        m = 320  # maildrop size
        await self.push('+OK %s %s' % (n, m))

    @command('TRANSACTION')
    async def pop3_LIST(self, arg):
        if arg is None:
            await self.push('+OK scan listing follows')
            for n, message in enumerate(self.messages, 1):
                if message.deleted:
                    continue
                m = 120  # exact size of message
                await self.push('%s %s' % (n, m))
            await self.push('.')
        else:
            n = int(arg)
            m = 120  # exact size of message
            message = self.messages[n-1]
            if message is None or message.deleted:
                await self.push('-ERR no such message')
            else:
                await self.push('+OK %s %s' % (n, m))

    @command('TRANSACTION')
    async def pop3_UIDL(self, arg):
        if arg is None:
            await self.push('+OK scan listing follows')
            for n, message in enumerate(self.messages, 1):
                if message.deleted:
                    continue
                m = 'hej'  # unique id of message
                await self.push('%s %s' % (n, m))
            await self.push('.')
        else:
            n = int(arg)
            message = self.messages[n-1]
            m = 'hej'  # unique id of message
            if message is None or message.deleted:
                await self.push('-ERR no such message')
            else:
                await self.push('+OK %s %s' % (n, m))

    @command('TRANSACTION')
    async def pop3_RETR(self, arg):
        n = int(arg)
        await self.push('+OK message follows')
        for line in message:
            await self.push(line)
        await self.push('.')

    @command('TRANSACTION')
    async def pop3_DELE(self, arg):
        n = int(arg)
        if self.messages[n-1].deleted:
            await self.push('-ERR already deleted')
            return
        self.messages[n-1].deleted = True
        await self.push('+OK message deleted')

    @command('TRANSACTION')
    async def pop3_NOOP(self, arg):
        await self.push('+OK')

    @command('TRANSACTION')
    async def pop3_RSET(self, arg):
        for message in self.messages:
            message.deleted = False
        await self.push('+OK')

    @command('TRANSACTION')
    async def pop3_TOP(self, arg):
        msg, n = map(int, arg.split())
        await self.push('+OK top of message follows')
        for line in self.messages[msg][:n]:
            await self.push(line)
        await self.push('.')


HOST = '127.0.0.1'
PORT = 1100


if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR)
    log = logging.getLogger('mail.log')
    log.setLevel(logging.DEBUG)
    loop = asyncio.get_event_loop()
    loop.set_debug(enabled=True)
    server = loop.run_until_complete(
        loop.create_server(POP, host=HOST, port=PORT))
    log.info('Starting asyncio loop')
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    server.close()
    log.info('Completed asyncio loop')
    loop.run_until_complete(server.wait_closed())
    loop.close()
