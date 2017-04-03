from typing import List, Union
from email.message import Message
from mailtk.data import Mailbox, ThreadInfo


class AccountBase:
    @classmethod
    async def initialize(cls, loop, **kwargs):
        raise NotImplementedError

    async def list_folders(self) -> List[Mailbox]:
        raise NotImplementedError

    async def list_messages(self, mailbox: Mailbox) -> List[ThreadInfo]:
        raise NotImplementedError

    async def fetch_message(self, threadinfo: ThreadInfo) -> Union[Message, bytes]:
        raise NotImplementedError
