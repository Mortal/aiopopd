import asyncio


class WidgetMixin:
    def event_cb(self, coro_function):
        async def wrapper(ev):
            try:
                return await coro_function(ev)
            except Exception:
                return self.handle_exception()

        def callback(ev):
            asyncio.ensure_future(wrapper(ev), loop=self.loop)

        return callback

    def handle_exception(self):
        return self.master.handle_exception()

    def bind_async(self, *args):
        'bind_async([target,] event, coro) -> register coro on target.bind'
        if len(args) == 2:
            event, callback = args
            target = self
        elif len(args) == 3:
            target, event, callback = args
        else:
            raise TypeError('bind_async expected 2 or 3 arguments')
        return target.bind(event, self.event_cb(callback))

    @property
    def loop(self):
        return self.master.loop

    @property
    def style(self):
        return self.master.style

    @property
    def controller(self):
        return self.master.controller
