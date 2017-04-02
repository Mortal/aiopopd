import tkinter.ttk
from mailtk.gui.mixin import WidgetMixin
from mailtk.gui.autoscrollbar import AutoScrollbar
import email
from mailtk.util import decode_any_header
from mailtk.gui.bmp import bmp_call


class Message(tkinter.Frame, WidgetMixin):
    HEADERS = '''From To Cc Subject Date Reply-To Sender User-Agent X-Mailer
    Newsgroups Followup-To Organization X-Newsreader'''.split()

    def __init__(self, parent):
        super().__init__(parent)
        self.scrollbar = AutoScrollbar(self, orient=tkinter.VERTICAL)
        self.txt = tkinter.Text(self, state=tkinter.DISABLED,
                                yscrollcommand=self.scrollbar.set)
        self.txt.configure(**self.style.configure('Message.Text'))
        self.scrollbar.config(command=self.txt.yview)

        self.txt.grid(row=0, column=0, sticky='news')
        self.scrollbar.grid(row=0, column=1, sticky='ns')
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    def set_message(self, message):
        if message is None:
            return self.set_value('')
        headers = [
            '%s: %s' % (k, str(decode_any_header(v)))
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
        self.txt.configure(state=tkinter.NORMAL)
        self.txt.delete(1.0, tkinter.END)
        bmp_call(self.txt.insert, tkinter.END, text)
        self.txt.configure(state=tkinter.DISABLED)

    def handle_exception(self):
        raise
