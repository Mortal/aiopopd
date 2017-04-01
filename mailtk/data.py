from mailtk.namedtuple_with_abc import namedtuple


class ThreadInfo(namedtuple.abc):
    _fields = 'recipients subject date excerpt'

class ThreadAccount(ThreadInfo):
    _fields = 'account handle'


class Mailbox(namedtuple.abc):
    _fields = 'name delimiter flags'

class MailboxAccount(Mailbox):
    _fields = 'account'
