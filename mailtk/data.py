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


class Flag(Enum):
    read = 'read'
    unread = 'unread'
    new = 'new'
    replied = 'replied'
    forwarded = 'forwarded'


class ThreadInfo(namedtuple.abc):
    _fields = 'recipients subject date excerpt flag size'


class Mailbox(namedtuple.abc):
    _fields = 'name'
