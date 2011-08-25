#!/usr/bin/env python
from clusto import script_helpers
import clusto

import sys


class ListPool(script_helpers.Shell):
    def _add_arguments(self, parser):
        parser.add_argument("-k", "--key", default='ip')
        parser.add_argument("-s", "--subkey", default='ipstring')
        parser.add_argument("-p", "--print-name", action="store_true", dest="print_name", default=False)
        parser.add_argument('pools', nargs='+')

    def add_subparser(self, subparsers):
        parser = self._setup_subparser(subparsers)
        self._add_arguments(parser)

    def run(self, args):
        for entity in clusto.get_from_pools(args.pools):
            name = [entity.name] if args.print_name else []
            attrs = name + entity.attr_values(key=args.key, subkey=args.subkey)
            print ' '.join(attrs)

def main():
    list_pool, args = script_helper.init_arguments(ListPool)
    return list_pool.run(args)

if __name__ == '__main__':
    sys.exit(main())
