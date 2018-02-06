import email
import poplib
import getpass
import argparse
import subprocess


def get_password(s):
    try:
        source, key = s.split(':', 1)
    except ValueError:
        raise ValueError('Format: pass:<name> or plain:<value>')
    if source == 'pass':
        return subprocess.check_output(('pass', key), universal_newlines=True).splitlines()[0]
    elif source == 'plain':
        return key
    else:
        raise ValueError('Format: pass:<name> or plain:<value>')


parser = argparse.ArgumentParser()
parser.add_argument('-H', '--hostname', default='localhost')
parser.add_argument('-n', '--port', default=1100, type=int)
parser.add_argument('-u', '--username', required=True)
parser.add_argument('-p', '--password-source', type=get_password, dest='password')
parser.add_argument('-d', '--delete', action='store_true')
parser.add_argument('-s', '--ssl', action='store_true')


def main():
    args = parser.parse_args()
    password = getpass.getpass() if args.password is None else args.password
    class_ = poplib.POP3_SSL if args.ssl else poplib.POP3
    client = class_(args.hostname, args.port)

    def invoke(method, *args, long=False):
        if method == 'pass_':
            print('>>> PASS ...')
        else:
            print('>>> %s%s' % (method, ''.join(' %s' % v for v in args)))
        try:
            result = getattr(client, method)(*args)
        except poplib.error_proto as exn:
            print('<<<', exn)
        else:
            if long:
                status, lines, octets = result
                print('<<<', status.decode())
                if method == 'retr':
                    message = email.message_from_bytes(b'\r\n'.join(lines))
                    for k, v in message.items():
                        print('<<< %s: %s' % (k, v))
                else:
                    for line in lines:
                        print('<<<', line.decode())
            else:
                print('<<<', result.decode() if isinstance(result, bytes) else result)

    invoke('getwelcome')
    invoke('capa')
    invoke('user', args.username)
    invoke('pass_', args.password)
    invoke('stat')
    invoke('list', long=True)
    invoke('uidl', long=True)
    invoke('retr', 1, long=True)
    invoke('dele', 1)
    invoke('noop')
    if not args.delete:
        invoke('rset')
    invoke('quit')


if __name__ == '__main__':
    main()
