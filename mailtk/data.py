from collections import namedtuple


ThreadInfo = namedtuple(
    'ThreadInfo', 'recipients subject date excerpt')

class ThreadAccount(namedtuple('ThreadAccount', 'inner account handle')):
    def __getattr__(self, k):
        return getattr(self.inner, k)


Mailbox = namedtuple('Mailbox', 'name delimiter flags')

class MailboxAccount(namedtuple('MailboxAccount', 'inner account')):
    def __getattr__(self, k):
        return getattr(self.inner, k)
