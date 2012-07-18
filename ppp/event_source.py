#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: tw=120

import tornado
import pty
import os
import signal
import traceback
from tornado import web, httpserver

import base64

class Read(web.RequestHandler):
    def initialize(self):
        self._fd = None
        self._pid = None

    def on_finish(self):
        if self._fd is not None:
            os.close(self._fd)
        if self._pid is not None:
            os.kill(self._pid, signal.SIGKILL)
            # TODO: signalfd
            os.wait4(self._pid, 0)

    #@tornado.web.asynchronous
    def push_keepalive(self):
        self.write(b':\n\n')
        self.flush()

    def _splice(self, event):
        if event & tornado.ioloop.IOLoop.READ:
            data = os.read(self._fd, 65536)
            if data:
                self.write(b'data:')
                self.write(self._encoder(data))
                self.write(b'\n\n')
                self.flush()
        if event & tornado.ioloop.IOLoop.ERROR:
            os.close(self._fd)
            self._fd = None
            self.finish()

    @tornado.web.asynchronous
    def get(self):
        #self._keepalive = tornado.ioloop.PeriodicCallback(self.push_keepalive, 10 * 1000); # milliseconds
        self._encoder = base64.b64encode
        (self._pid, self._fd) = pty.fork()
        if not self._pid:
            #child
            try:
                os.closerange(3, 1024)
                os.execv('/usr/sbin/pppd', ['pppd'])
                #os.execv('/bin/sh', ['sh', '-c', 'echo qwe; sleep 1; echo rty'])
            except:
                os.write(2, traceback.format_exc())
            finally:
                os._exit(os.EX_OSERR)

        self.set_header("Content-Type", "text/event-stream")
        self.set_header("Cache-Control", "no-cache")
        self.flush()
        tornado.ioloop.IOLoop.instance().add_handler(self._fd, lambda fd, event: self._splice(event), tornado.ioloop.IOLoop.READ)
        #self._keepalive.start()


def main():
    application = web.Application([
        ('/read', Read),
    ], debug=False)

    http_server = httpserver.HTTPServer(application).listen(8080, '0.0.0.0')
    tornado.ioloop.IOLoop.instance().start()
    return http_server

if __name__ == '__main__':
    main()
