import os
import pwd
import asyncio
import threading

from aiopopd.pop import Pop3, log


class Controller:
    def __init__(self, handler, loop=None, hostname=None, port=1100, *,
                 ready_timeout=1.0, ssl_context=None, setuid=False):
        self.handler = handler
        self.hostname = '::1' if hostname is None else hostname
        self.port = port
        self.ssl_context = ssl_context
        self.loop = asyncio.new_event_loop() if loop is None else loop
        self.server = None
        self._thread = None
        self._thread_exception = None
        self.ready_timeout = os.getenv(
            'AIOPOPD_CONTROLLER_TIMEOUT', ready_timeout)
        self.setuid = setuid

    def factory(self):
        """Allow subclasses to customize the handler/server creation."""
        return Pop3(self.handler)

    def drop_privileges(self):
        if self.setuid:
            nobody = pwd.getpwnam('nobody').pw_uid
            os.setuid(nobody)

    def _run(self, ready_event):
        asyncio.set_event_loop(self.loop)
        try:
            self.server = self.loop.run_until_complete(
                self.loop.create_server(
                    self.factory, host=self.hostname, port=self.port,
                    ssl=self.ssl_context))
            self.drop_privileges()
        except Exception as error:
            self._thread_exception = error
            ready_event.set()
            return
        self.loop.call_soon(ready_event.set)
        self.loop.run_forever()
        self.server.close()
        self.loop.run_until_complete(self.server.wait_closed())
        self.loop.close()
        self.server = None

    def start(self):
        assert self._thread is None, 'POP3 daemon already running'
        ready_event = threading.Event()
        self._thread = threading.Thread(target=self._run, args=(ready_event,))
        self._thread.daemon = True
        self._thread.start()
        # Wait a while until the server is responding.
        ready_event.wait(self.ready_timeout)
        if self._thread_exception is not None:
            raise self._thread_exception
        self.log_start()

    def _stop(self):
        self.loop.stop()
        for task in asyncio.Task.all_tasks(self.loop):
            task.cancel()

    def stop(self):
        assert self._thread is not None, 'POP3 daemon not running'
        self.loop.call_soon_threadsafe(self._stop)
        self._thread.join()
        self._thread = None
        self.log_stop()

    def log_start(self):
        log.info("POP3 server listening on %s:%s",
                 self.hostname, self.port)

    def log_stop(self):
        log.info("POP3 server stopping")
