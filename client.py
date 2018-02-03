import poplib


def main():
    client = poplib.POP3('127.0.0.1', 1100)

    def invoke(method, *args):
        print('>>> %s%s' % (method, ''.join(' %s' % v for v in args)))
        try:
            result = getattr(client, method)(*args)
        except poplib.error_proto as exn:
            print('<<<', exn)
        else:
            print('<<<', result.decode())

    invoke('getwelcome')
    invoke('capa')
    invoke('user', 'luser')
    invoke('pass_', 'hunter2')
    invoke('stat')
    invoke('list')
    invoke('uidl')
    invoke('retr', 1)
    invoke('dele', 1)
    invoke('noop')
    invoke('rset')
    invoke('quit')


if __name__ == '__main__':
    main()
