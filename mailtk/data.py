'''
Note that subclassing of namedtuple works in a particular duck-typy fashion.
The base class Mailbox is subclassed as MailboxAccount and MailboxImap.
The IMAP account returns MailboxImap instances which are wrapped into
MailboxAccount instances by the controller, and the controller unwraps the
MailboxAccount into a MailboxImap when passing back to the account.
This works even though MailboxAccount subclasses Mailbox instead of
MailboxImap.
'''


from enum import Enum
from mailtk.namedtuple_with_abc import namedtuple


try:
    # Don't redefine when reloading mailtk/data.py
    Pending
except NameError:
    class Pending:
        '''
        Special value indicating that a field will be retrieved from a remote
        server.
        '''
        def __bool__(self):
            return False

        def __str__(self):
            return '<pending>'

        def __repr__(self):
            return '%s.%s' % (self.__module__, self.__class__.__name__)

    Pending = Pending()


class Flag(Enum):
    read = 'read'
    unread = 'unread'
    new = 'new'
    replied = 'replied'
    forwarded = 'forwarded'


class ThreadInfo(namedtuple.abc):
    _fields = ('flag', 'size', 'date', 'sender', 'recipients', 'subject',
               'children', 'excerpt')


class Mailbox(namedtuple.abc):
    _fields = 'name children'
