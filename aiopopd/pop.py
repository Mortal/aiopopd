import socket
import asyncio
import logging
import functools


VERSION = '0.1'
IDENT = 'Python POP3 {}'.format(VERSION)
log = logging.getLogger('aiopopd.log')
MISSING = object()


def command(state):
    def decorator(fn):
        fn.command_state = state
        return fn

    return decorator


class Pop3(asyncio.StreamReaderProtocol):
    __ident__ = 'aiopopd'

    def __init__(self, handler, *, hostname=None, loop=None):
        self.hostname = hostname or socket.getfqdn()
        self.loop = loop or asyncio.get_event_loop()
        super().__init__(
            asyncio.StreamReader(loop=self.loop),
            client_connected_cb=self._client_connected_cb,
            loop=self.loop)
        self.event_handler = handler

    async def _call_handler_hook(self, command, *args):
        hook = getattr(self.event_handler, 'handle_' + command, None)
        if hook is None:
            return MISSING
        status = await hook(self, *args)
        return status

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
        if hasattr(self.event_handler, 'handle_exception'):
            status = await self.event_handler.handle_exception(error)
            return status
        else:
            log.exception('POP3 session exception')
            status = '-ERR Error: ({}) {}'.format(
                error.__class__.__name__, str(error))
            return status

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
        except Exception as error:
            try:
                status = await self.handle_exception(error)
            except Exception as error:
                try:
                    log.exception('Exception in handle_exception()')
                    status = '-ERR Error: ({}) {}'.format(
                        error.__class__.__name__, str(error))
                except Exception:
                    status = '-ERR Error: Cannot describe error'
            await self.push(status)

    @staticmethod
    def parse_message_number(arg):
        if arg is None:
            raise ValueError(arg)
        n = int('+' + arg)
        if n < 1:
            raise ValueError(arg)
        return n

    @command('AUTHORIZATION')
    async def pop3_USER(self, arg):
        # RFC states each arg contains no spaces and is at most 40 characters,
        # but we ignore that restriction here.
        if arg is None:
            await self.push('-ERR Syntax: USER <username>')
            return
        if self.username is not None:
            await self.push('-ERR already supplied username')
            return
        status = await self._call_handler_hook('USER', arg)
        if status is MISSING:
            self.username = arg
            status = '+OK name is a valid mailbox'
        await self.push(status)

    @command('AUTHORIZATION')
    async def pop3_PASS(self, arg):
        if arg is None:
            await self.push('-ERR Syntax: PASS <password>')
            return
        if self.username is None:
            await self.push('-ERR must supply username first')
            return
        status = await self._call_handler_hook('PASS', self.username, arg)
        if status is MISSING:
            self.password = arg
            self.state = 'TRANSACTION'
            status = '+OK'
        await self.push(status)

    @command('AUTHORIZATION')
    async def pop3_APOP(self, arg):
        status = await self._call_handler_hook('APOP', arg)
        await self.push(
            '-ERR APOP not implemented'
            if status is MISSING else status)

    async def pop3_QUIT(self, arg):
        if arg is not None:
            await self.push('-ERR Syntax: QUIT')
            return
        status = await self._call_handler_hook('QUIT')
        await self.push('+OK Bye' if status is MISSING else status)
        self._handler_coroutine.cancel()
        self.transport.close()

    @command('TRANSACTION')
    async def pop3_STAT(self, arg):
        if arg is not None:
            await self.push('-ERR Syntax: STAT')
            return
        status = await self._call_handler_hook('STAT')
        await self.push('+OK 0 0' if status is MISSING else status)

    @command('TRANSACTION')
    async def pop3_LIST(self, arg):
        if arg is None:
            await self.push('+OK scan listing follows')
            n = 1
            while True:
                try:
                    size = self._call_handler_hook('LIST', n)
                except IndexError:
                    break
                if size is MISSING:
                    break
                if size is not None:
                    await self.push('%s %s' % (n, size))
                n += 1
            await self.push('.')
        else:
            try:
                n = self.parse_message_number(arg)
            except ValueError:
                await self.push('-ERR Syntax: LIST [n]')
                return
            try:
                size = self._call_handler_hook('LIST', n)
            except IndexError:
                await self.push('-ERR no such message')
                return
            if size is None:
                await self.push('-ERR no such message')
            else:
                await self.push('+OK %s %s' % (n, size))

    @command('TRANSACTION')
    async def pop3_UIDL(self, arg):
        if arg is None:
            await self.push('+OK unique-id listing follows')
            n = 1
            while True:
                try:
                    uid = self._call_handler_hook('UIDL', n)
                except IndexError:
                    break
                if uid is MISSING:
                    break
                if uid:
                    await self.push('%s %s' % (n, uid))
                n += 1
            await self.push('.')
        else:
            try:
                n = self.parse_message_number(arg)
            except ValueError:
                await self.push('-ERR Syntax: UIDL [n]')
                return
            try:
                uid = self._call_handler_hook('UIDL', n)
            except IndexError:
                await self.push('-ERR no such message')
                return
            if uid is MISSING:
                await self.push('-ERR no such message')
            else:
                await self.push('+OK %s %s' % (n, uid))

    @command('TRANSACTION')
    async def pop3_RETR(self, arg):
        try:
            n = self.parse_message_number(arg)
        except ValueError:
            await self.push('-ERR Syntax: RETR <n>')
            return
        status = self._call_handler_hook('RETR', n)
        if status is MISSING:
            await self.push('-ERR no such message')

    @command('TRANSACTION')
    async def pop3_DELE(self, arg):
        try:
            n = self.parse_message_number(arg)
        except ValueError:
            await self.push('-ERR Syntax: DELE <n>')
            return
        status = self._call_handler_hook('DELE', n)
        await self.push('+OK deleted' if status is MISSING else status)

    @command('TRANSACTION')
    async def pop3_NOOP(self, arg):
        if arg is not None:
            await self.push('-ERR Syntax: NOOP')
            return
        status = self._call_handler_hook('NOOP')
        await self.push('+OK' if status is MISSING else status)

    @command('TRANSACTION')
    async def pop3_RSET(self, arg):
        if arg is not None:
            await self.push('-ERR Syntax: RSET')
            return
        status = self._call_handler_hook('RSET')
        await self.push('+OK' if status is MISSING else status)

    @command('TRANSACTION')
    async def pop3_TOP(self, arg):
        try:
            n_str, lines_str = arg.split(' ')
            n = self.parse_message_number(n_str)
            lines = int('+' + lines_str)  # allowed to be zero
        except ValueError:
            await self.push('-ERR Syntax: TOP <n> <lines>')
            return
        status = self._call_handler_hook('TOP', n, lines)
        if status is MISSING:
            await self.push('-ERR no such message')
