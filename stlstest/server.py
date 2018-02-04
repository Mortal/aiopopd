import os
import ssl
import asyncio
import logging
import argparse
import subprocess
from aiopopd.pop import Pop3
from aiopopd.imap import ImapHandler


parser = argparse.ArgumentParser()
parser.add_argument('-H', '--imap-hostname', required=True)
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

    # Create cert and key if they don't exist
    if not os.path.exists('cert.pem') and not os.path.exists('key.pem'):
        subprocess.call('openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem ' +
                        '-days 365 -nodes -subj "/CN=localhost"', shell=True)

    # Load SSL context
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain('cert.pem', 'key.pem')

    def factory():
        handler = ImapHandler(args.imap_hostname,
                              args.imap_port,
                              args.imap_ssl)
        return Pop3(handler, require_starttls=True, tls_context=context)

    server = loop.run_until_complete(
        loop.create_server(factory, host=HOST, port=args.listen_port))
    log.info('Starting asyncio loop')
    log.info('Consider using swaks for testing: ' +
             'swaks -tls -t test --server localhost:%s' % args.listen_port)
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
