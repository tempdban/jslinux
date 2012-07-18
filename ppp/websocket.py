#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: tw=120

from __future__ import absolute_import

import tornado
import pty
import os
import traceback

from tornado import websocket, httpserver

class EchoWebSocket(websocket.WebSocketHandler):
    def open(self):
        err = os.dup(2) # forkpty have the BUG: it duplicates terminal also to stderr of child, so save our stderr here.
        (self._pid, self._fd) = pty.fork()
        if self._pid:
            # parent
            os.close(err)
            tornado.ioloop.IOLoop.instance().add_handler(self._fd, lambda fd, event: self._splice(event), tornado.ioloop.IOLoop.READ|tornado.ioloop.IOLoop.ERROR)
            return
        #child
        try:
            os.dup2(err, 2) # restore original stderr
            os.closerange(3, 1024)
            os.execv('/usr/sbin/pppd', ['pppd', 'nodetach', 'debug', 'logfile', '/dev/stderr'])
        except:
            os.write(2, traceback.format_exc())
        finally:
            os._exit(os.EX_OSERR)

    def __cleanup(self):
        tornado.ioloop.IOLoop.instance().remove_handler(self._fd)
        os.close(self._fd)
        self._fd = None

    def _splice(self, event):
        if event & tornado.ioloop.IOLoop.READ:
            data = os.read(self._fd, 65536)
            if data:
                self.write_message(data, binary=True)
        if event & tornado.ioloop.IOLoop.ERROR:
            self.__cleanup()
            self.close()

    def on_message(self, message):
        os.write(self._fd, message)

    def on_close(self):
        if self._fd is not None:
            self.__cleanup()

class MainPage(tornado.web.RequestHandler):
    def get(self):
        self.finish('''<!DOCTYPE html>
        <script>
            var ws = new WebSocket("ws://10.80.1.20:8080/websocket");
            ws.onmessage = function (evt) {
                console.log(evt.data);
                ws.send(evt.data); //loop data back
            };
        </script>
        ''')

def main():
    application = tornado.web.Application([
        ('/websocket', EchoWebSocket),
        ('/', MainPage),
    ], debug=False)

    http_server = httpserver.HTTPServer(application).listen(8080, '10.80.1.20')
    tornado.ioloop.IOLoop.instance().start()
    return http_server

if __name__ == '__main__':
    main()
