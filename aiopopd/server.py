import os
import json
import time
import logging
import argparse
from aiopopd.pop import Pop3
from aiopopd.imap import ImapHandler, ImapBackend
from aiopopd.controller import Controller
from aiopopd.main import get_ssl_context, SystemdFormatter


class ImapHandlerFile(ImapHandler):
    def __init__(self, path, **kwargs):
        super().__init__(**kwargs)
        self.path = path

    async def get_backend(self, username, password):
        if '/' in username or username.startswith('.'):
            raise ValueError('invalid username')
        try:
            with open(os.path.join(self.path, username)) as fp:
                config = json.load(fp)
        except FileNotFoundError:
            raise ValueError('unknown username')
        backend = ImapBackend(loop=self.loop, host=config['hostname'],
                              port=config['port'], ssl=config.get('ssl', True))
        await backend.connect()
        await backend.login(config.get('username', username), password)
        return backend


parser = argparse.ArgumentParser()
parser.add_argument('-p', '--path', required=True)
parser.add_argument('-r', '--listen-all', action='store_true')
parser.add_argument('-P', '--listen-port', required=True, type=int)
parser.add_argument('-n', '--no-setuid', action='store_false', dest='setuid')
parser.add_argument('-l', '--systemd-logging', action='store_true')
parser.add_argument('-d', '--hostname')
parser.add_argument('--ssl-key')
parser.add_argument('--ssl-cert')
parser.add_argument('--ssl-generate', action='store_true')


def main():
    args = parser.parse_args()
    ssl_context = get_ssl_context(args)
    logging.basicConfig(level=logging.ERROR)
    log = logging.getLogger('aiopopd.log')
    log.setLevel(logging.DEBUG)

    if args.systemd_logging:
        handler, = logging.getLogger().handlers
        handler.setFormatter(SystemdFormatter())

    def factory():
        return Pop3(ImapHandlerFile(args.path), hostname=args.hostname)

    hostname = '0.0.0.0' if args.listen_all else '::1'
    controller = Controller(None, hostname=hostname, port=args.listen_port,
                            ssl_context=ssl_context, setuid=args.setuid)
    controller.factory = factory
    controller.loop.set_debug(enabled=True)
    try:
        controller.start()
    except PermissionError:
        raise SystemExit(
            'Cannot setuid "nobody"; try running with -n option.')
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        pass
    controller.stop()


if __name__ == '__main__':
    main()
