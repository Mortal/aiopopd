import tkinter.ttk
from aiotkinter import WidgetMixin
import email


class Message(tkinter.Text, WidgetMixin):
    HEADERS = '''From To Cc Subject Date Reply-To Sender User-Agent X-Mailer
    Newsgroups Followup-To Organization X-Newsreader'''.split()

    def __init__(self, parent):
        super().__init__(parent, state=tkinter.DISABLED)

    def set_message(self, message_source):
        message = email.message_from_bytes(message_source)
        headers = [
            '%s: %s' % (k, v)
            for k in self.HEADERS
            for v in (message.get_all(k) or ())
        ]

        parts = ['\n'.join(headers)]

        for part in message.walk():
            maintype = part.get_content_maintype()
            if maintype == 'text':
                bpayload = part.get_payload(decode=True)
                try:
                    payload = bpayload.decode(
                        part.get_param('charset', 'ascii'), 'replace')
                except LookupError:
                    payload = bpayload.decode('ascii', 'replace')
                parts.append(payload.replace('\r', ''))

        self.set_value('\n\n'.join(parts))

    def set_value(self, text):
        self.configure(state=tkinter.NORMAL)
        self.delete(1.0, tkinter.END)
        self.insert(tkinter.END, text)
        self.configure(state=tkinter.DISABLED)

    def handle_exception(self):
        raise
