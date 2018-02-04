from aiopopd.pop import Pop3


HOST = '127.0.0.1'
PORT = 1100


if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR)
    log = logging.getLogger('aiopopd.log')
    log.setLevel(logging.DEBUG)
    loop = asyncio.get_event_loop()
    loop.set_debug(enabled=True)
    server = loop.run_until_complete(
        loop.create_server(Pop3, host=HOST, port=PORT))
    log.info('Starting asyncio loop')
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    server.close()
    log.info('Completed asyncio loop')
    loop.run_until_complete(server.wait_closed())
    loop.close()
