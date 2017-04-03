import os
import queue
import base64
import pprint
import quopri
import asyncio
import httplib2
import threading
import email.message

from mailtk.data import ThreadInfo, Mailbox
from mailtk.accounts.base import AccountBase

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage


# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'client_secret.json')
APPLICATION_NAME = 'Gmail API Python Quickstart'


class MailboxGmail(Mailbox):
    _fields = 'label'


class ThreadInfoGmail(ThreadInfo):
    _fields = 'data'


class GmailAccount(AccountBase):
    @classmethod
    async def initialize(cls, loop, credential_path=None):
        if credential_path is None:
            credential_path = '~/.config/mailtk/gmail-creds.json'
        credential_path = os.path.expanduser(credential_path)
        credential_dir = os.path.dirname(credential_path)
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        account = cls(loop, credential_path)
        await account.connect()
        return account

    BREAK = object()
    NOOP = object()

    def __init__(self, loop, credential_path):
        self._loop = loop
        self._credential_path = credential_path

        self._command_queue = queue.Queue()
        self._response_queue = queue.Queue()
        self._ready_r, self._ready_w = os.pipe()
        loop.add_reader(self._ready_r, self._ready)
        self._thread = threading.Thread(None, self._run)
        self._breaking = False

    async def connect(self):
        self._thread.start()
        await self._call(self.NOOP)

    async def disconnect(self):
        await self._call(self.BREAK)
        self._thread.join()

    async def _call(self, method, *args):
        if self._breaking:
            raise Exception('connection is closing')
        future = asyncio.Future(loop=self._loop)
        self._command_queue.put_nowait((future, method, args))
        if method is self.BREAK:
            self._breaking = True
        result = await future
        if isinstance(result, Exception):
            raise result
        return result

    def _run(self):
        # Run commands in thread
        try:
            credentials = self._get_credentials()
            http = credentials.authorize(httplib2.Http())
            service = discovery.build('gmail', 'v1', http=http)
        except Exception as exn:
            future, method, args = self._command_queue.get()
            self._response_queue.put((future, exn))
            self._command_queue.task_done()
            os.write(self._ready_w, b'x')
            return
        try:
            while True:
                future, method, args = self._command_queue.get()
                if method is self.BREAK:
                    break
                elif method is self.NOOP:
                    result = None
                else:
                    # TODO check if future is cancelled
                    try:
                        result = method(self, service, *args)
                    except Exception as exn:
                        result = exn
                self._response_queue.put((future, result))
                self._command_queue.task_done()
                os.write(self._ready_w, b'x')
        finally:
            del service
            del http
            del credentials

        assert method is self.BREAK
        self._response_queue.put((future, None))
        self._command_queue.task_done()
        os.write(self._ready_w, b'x')

    def _ready(self):
        os.read(self._ready_r, 1)
        future, result = self._response_queue.get_nowait()
        if not future.cancelled():
            future.set_result(result)
        self._response_queue.task_done()

    def _get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """
        store = Storage(self._credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
            flow.user_agent = APPLICATION_NAME
            flags = tools.argparser.parse_args([])
            credentials = tools.run_flow(flow, store, flags)
            # print('Storing credentials to ' + credential_path)
        return credentials

    def rpc(method):
        async def wrapper(self, *args):
            return await self._call(method, *args)

        return wrapper

    @rpc
    def list_folders(self, service):
        backend = service.users().labels().list(userId='me').execute()
        labels = backend.get('labels', [])
        result = [MailboxGmail(Mailbox(l['name'], []), l)
                  for l in labels]
        result.sort(key=lambda m: m.name)
        return result

    @rpc
    def list_messages(self, service, folder: MailboxGmail):
        label_id = folder.label['id']
        backend = service.users().threads().list(userId='me',
                                                 labelIds=[label_id]).execute()
        threads = []
        for data in backend['threads']:
            thread_info = ThreadInfo(
                flag=None,
                size=None,
                date=None,
                sender=None,
                recipients=None,
                subject=None,
                children=[],
                excerpt=data['snippet'])
            threads.append(ThreadInfoGmail(thread_info, data))
        return threads

    @rpc
    def fetch_message(self, service, threadinfo: ThreadInfoGmail):
        thread = threadinfo.data
        backend = service.users().threads().get(
            userId='me',
            id=thread['id'],
            format='full'
        ).execute()
        return construct_gmail_message(backend['messages'][0]['payload'])


def construct_gmail_message(payload):
    message = email.message.Message()
    for header in payload['headers']:
        message[header['name']] = header['value']
    if message.get_content_maintype() == 'multipart':
        message.set_payload(
            [construct_gmail_message(part)
             for part in payload['parts']])
    else:
        cte = message.get('Content-Transfer-Encoding')
        if cte is not None:
            del message['Content-Transfer-Encoding']
            message['X-Original-Content-Transfer-Encoding'] = cte
        try:
            external_id = payload['body']['attachmentId']
            ct = message.get_content_type()
            message.replace_header('Content-Type', 'text/plain')
            message.set_payload(
                'Attachment with type %s, ID %r omitted; retrieve separately' %
                (ct, external_id))
        except KeyError:
            body = payload['body']['data']
            body += '=' * (4 - len(body) % 4)
            message.set_payload(base64.urlsafe_b64decode(body))
    return message
