from mailtk.namedtuple_with_abc import namedtuple


class ThreadInfo(namedtuple.abc):
    _fields = 'recipients subject date excerpt'


class Mailbox(namedtuple.abc):
    _fields = 'name'
