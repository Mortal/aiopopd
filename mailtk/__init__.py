import os
import asyncio
import subprocess
from concurrent.futures import ThreadPoolExecutor
from aiotkinter import wrapper
from mailtk.gui import MailGui
from mailtk.imap import ImapAccount


async def run_pass(loop: asyncio.BaseEventLoop, arg):
    stdout = await loop.run_in_executor(
        None, lambda: subprocess.check_output(
            ('pass', arg), stdin=subprocess.DEVNULL,
            universal_newlines=True))
    return stdout.splitlines()[0]


async def get_imap_config(loop: asyncio.BaseEventLoop):
    try:
        host, port, user, pass_arg = os.environ['MAILTK'].split(':')
        password = await run_pass(loop, pass_arg)
        ssl = not os.environ.get('MAILTK_INSECURE')
    except KeyError:
        # ./asimapd.py --test_mode --foreground --no_ssl
        with open('../asimap/test_mode/test_mode_addr.txt') as fp:
            host, port = fp.read().strip().split(':')
        with open('../asimap/test_mode/test_mode_creds.txt') as fp:
            user, password = fp.read().strip().split(':')
        ssl = False
    return host, int(port), user, password, ssl


async def imap_test(root: MailGui, loop):
    root.message.set_value('Getting IMAP config')
    host, port, user, password, ssl = await get_imap_config(loop)
    root.message.set_value('Got password of length %s' % len(password))
    async with ImapAccount(loop, host, port, ssl) as imap:
        root.message.set_value('Connected to IMAP, capabilities %r' %
                               (imap.capabilities,))
        await imap.login(user, password)
        root.message.set_value('Logged in as %r' % (user,))
        mailboxes = await imap.list()
        root.message.set_value(repr(mailboxes))
        print(mailboxes)
        root.set_folders(mailboxes)
        if 'INBOX' not in mailboxes:
            code, msgs = await imap.create('INBOX')
            root.message.set_value(repr((mailboxes, code, msgs)))


async def exceptions_to_message(root, coro):
    try:
        return await coro
    except Exception:
        import traceback
        root.message.set_value(traceback.format_exc())


@wrapper
def main(loop: asyncio.BaseEventLoop):
    executor = ThreadPoolExecutor()
    loop.set_default_executor(executor)
    root = MailGui(loop)
    root.protocol('WM_DELETE_WINDOW', loop.stop)
    asyncio.ensure_future(
        exceptions_to_message(root, imap_test(root, loop)), loop=loop)
    return root
