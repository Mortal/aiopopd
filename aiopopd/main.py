import os
import ssl
import logging
import argparse
import subprocess
from aiopopd.pop import Pop3
from aiopopd.imap import ImapHandlerFixed
from aiopopd.controller import Controller


parser = argparse.ArgumentParser()
parser.add_argument('-H', '--imap-hostname', required=True)
parser.add_argument('-p', '--imap-port', required=True, type=int)
parser.add_argument('-s', '--imap-ssl', action='store_true')
parser.add_argument('-P', '--listen-port', required=True, type=int)
parser.add_argument('--ssl-key')
parser.add_argument('--ssl-cert')
parser.add_argument('--ssl-generate', action='store_true')


def get_ssl_context(args):
    if not args.ssl_key and not args.ssl_cert:
        return None
    if not args.ssl_key or not args.ssl_cert:
        raise SystemExit('Both --ssl-key and --ssl-cert must be specified')

    # Create cert and key if they don't exist
    generate = (args.ssl_generate and
                not os.path.exists(args.ssl_cert) and
                not os.path.exists(args.ssl_key))

    if generate:
        subprocess.check_call(
            ['openssl', 'req', '-x509', '-newkey', 'rsa:4096',
             '-keyout', args.ssl_key, '-out', args.ssl_cert, '-days', '365',
             '-nodes', '-subj', '/CN=localhost'])

    # Load SSL context
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(args.ssl_cert, args.ssl_key)
    return context


def main():
    args = parser.parse_args()
    ssl_context = get_ssl_context(args)
    logging.basicConfig(level=logging.ERROR)
    log = logging.getLogger('aiopopd.log')
    log.setLevel(logging.DEBUG)

    def factory():
        return Pop3(ImapHandlerFixed(args.imap_hostname,
                                     args.imap_port,
                                     args.imap_ssl))

    controller = Controller(None, port=args.listen_port, ssl_context=ssl_context)
    controller.factory = factory
    controller.loop.set_debug(enabled=True)
    controller.start()
    print('Server started; press Return to stop')
    input('')
    controller.stop()


if __name__ == '__main__':
    main()
