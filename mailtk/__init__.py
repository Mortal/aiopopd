import asyncio
from concurrent.futures import ThreadPoolExecutor
from aiotkinter import wrapper
from mailtk.gui import MailGui
from mailtk.controller import Controller
from mailtk.accounts import get_accounts


@wrapper
def main(loop: asyncio.BaseEventLoop):
    executor = ThreadPoolExecutor()
    loop.set_default_executor(executor)
    root = MailGui(loop)
    root.protocol('WM_DELETE_WINDOW', loop.stop)
    accounts = dict(get_accounts())
    controller = Controller(loop, accounts, root)
    return root
