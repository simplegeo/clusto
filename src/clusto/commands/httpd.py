#!/usr/bin/env python
from wsgiref.simple_server import make_server, WSGIRequestHandler
import sys

from clusto.services.config import conf
from clusto.services.http import ClustoApp
from clusto import script_helper
import clusto


class ClustoHTTP(script_helper.Script):
    def __init__(self):
        script_helper.Script.__init__(self)

    def _add_arguments(self, parser):
        parser.add_argument('-a', '--address', help='Address to bind to (default: 0.0.0.0)', default='0.0.0.0')
        parser.add_argument('-p', '--port', help='Port to bind to (default: 9996)', default=9996, type=int)

    def add_subparser(self, subparsers):
        parser = self._setup_subparser(subparsers)
        self._add_arguments(parser)

    def run(self, args):
        app = ClustoApp()

        # Disable reverse DNS upon request. It's just stupid.
        wsgi = WSGIRequestHandler
        def address_string(self):
            return self.client_address[0]
        wsgi.address_string = address_string

        server = make_server(args.address, args.port, app, handler_class=wsgi)
        server.serve_forever()


def main():
    http, args = script_helper.init_arguments(ClustoHTTP)
    return http.run(args)


if __name__ == '__main__':
    sys.exit(main())
