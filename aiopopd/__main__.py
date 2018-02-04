import asyncio
import logging
import argparse
from aiopopd.pop import Pop3
from aiopopd.imap import ImapHandler


parser = argparse.ArgumentParser()
parser.add_argument('-h', '--imap-hostname', required=True)
parser.add_argument('-p', '--imap-port', required=True, type=int)
parser.add_argument('-s', '--imap-ssl', action='store_true')
parser.add_argument('-P', '--listen-port', required=True, type=int)
HOST = '127.0.0.1'


def main():
    args = parser.parse_args()
    logging.basicConfig(level=logging.ERROR)
    log = logging.getLogger('aiopopd.log')
    log.setLevel(logging.DEBUG)
    loop = asyncio.get_event_loop()
    loop.set_debug(enabled=True)

    def factory():
        return Pop3(ImapHandler(args.imap_hostname,
                                args.imap_port,
                                args.imap_ssl))

    server = loop.run_until_complete(
        loop.create_server(factory, host=HOST, port=args.listen_port))
    log.info('Starting asyncio loop')
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    server.close()
    log.info('Completed asyncio loop')
    loop.run_until_complete(server.wait_closed())
    loop.close()


if __name__ == '__main__':
    main()
