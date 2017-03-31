import os
import asyncio
import subprocess
from concurrent.futures import ThreadPoolExecutor
from aiotkinter import wrapper
from mailtk.gui import MailGui
from mailtk.imap import ImapAccount
from mailtk.controller import Controller


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
        ## ./asimapd.py --test_mode --foreground --no_ssl
        # with open('../asimap/test_mode/test_mode_addr.txt') as fp:
        #     host, port = fp.read().strip().split(':')
        # with open('../asimap/test_mode/test_mode_creds.txt') as fp:
        #     user, password = fp.read().strip().split(':')

        # Dovecot
        with open('/etc/dovecot/passwd') as fp:
            user, password_tag, *rest = fp.readline().split(':')
        password = password_tag.replace('{PLAIN}', '')
        host, port = '127.0.0.1', 143
        ssl = False
    return host, int(port), user, password, ssl


async def get_imap(controller):
    loop = controller.loop
    controller.log_debug('Getting IMAP config')
    config = await get_imap_config(loop)
    host, port, user, password, ssl = config
    controller.log_debug('Got password of length %s' % len(password))
    imap = ImapAccount(loop, host, port, ssl)
    await imap.connect()
    controller.log_debug('Connected to IMAP, capabilities %r' %
                         (imap.capabilities,))
    await imap.backend.login(user, password)
    controller.log_debug('Logged in as %r' % (user,))
    return imap
    # await imap.backend.login(user, password)
    # mailboxes = await imap.list()
    # controller.log_debug(repr(mailboxes))
    # print(mailboxes)
    # root.set_folders(mailboxes)
    # if 'INBOX' not in mailboxes:
    #     code, msgs = await imap.backend.create('INBOX')
    #     controller.log_debug(repr((mailboxes, code, msgs)))


# async def exceptions_to_message(root, coro):
#     try:
#         return await coro
#     except Exception:
#         import traceback
#         root.message.set_value(traceback.format_exc())


@wrapper
def main(loop: asyncio.BaseEventLoop):
    executor = ThreadPoolExecutor()
    loop.set_default_executor(executor)
    root = MailGui(loop)
    root.protocol('WM_DELETE_WINDOW', loop.stop)
    accounts = {'imap': get_imap}
    controller = Controller(loop, accounts, root)
    # asyncio.ensure_future(
    #     exceptions_to_message(root, imap_test(root, loop)), loop=loop)
    return root
