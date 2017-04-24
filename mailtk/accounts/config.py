import asyncio
import importlib
import subprocess
import configparser


class SubprocessBackend:
    def __init__(self, *cmdline, maxcalls=1):
        self.cmdline = tuple(cmdline)
        self.maxcalls = maxcalls
        self._calls = asyncio.Semaphore(maxcalls)

    async def __call__(self, arg, loop):
        await self._calls.acquire()
        try:
            stdout = await loop.run_in_executor(
                None, lambda: subprocess.check_output(
                    self.cmdline + (arg,), stdin=subprocess.DEVNULL,
                    universal_newlines=True))
            return stdout.splitlines()[0]
        finally:
            self._calls.release()


PASSWORD_BACKENDS = {
    'plain': asyncio.coroutine(lambda arg, loop: arg),
    'pass': SubprocessBackend('pass'),
}


async def get_password_from_spec(loop, spec):
    kind, arg = spec.split(':')
    try:
        backend = PASSWORD_BACKENDS[kind]
    except KeyError:
        raise ValueError(kind)
    return await backend(arg, loop=loop)


def get_account(fields):
    fields = dict(**fields)
    module_name, sep, class_name = fields.pop('class').rpartition('.')
    module = importlib.import_module(module_name)
    class_ = getattr(module, class_name)
    password_spec = fields.pop('password', None)

    async def initialize(controller):
        if password_spec is not None:
            password = await get_password_from_spec(
                controller.loop, password_spec)
            fields['password'] = password
        return await class_.initialize(controller.loop, **fields)

    return initialize


def get_accounts():
    config = configparser.ConfigParser()
    config.read('accounts.ini')
    for account_name in config.sections():
        yield account_name, get_account(config[account_name])
