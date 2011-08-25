#!/usr/bin/env python
# -*- mode: python; sh-basic-offset: 4; indent-tabs-mode: nil; coding: utf-8 -*-
# vim: tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8

import argparse
import re
import sys

import clusto
from clusto import script_helper

JSON=False
YAML=False
try:
    import yaml
    YAML=True
except ImportError:
    pass

try:
    import simplejson as json
    JSON=True
except ImportError:
    try:
        import json
        JSON=True
    except:
        pass

PROPERTY_MAP = (
    ('Name', 'name'),
    ('Type', 'type'),
    ('Driver', 'driver'),
)

class Info(script_helper.Script):
    '''
    This is a script that displays information about a certain object
    (or list of objects) and displays it to stdout.
    '''

    def __init__(self):
        script_helper.Script.__init__(self)

    def _add_arguments(self, parser):
        parser.add_argument('items', nargs='*', metavar='item', help='List of one or more objects to show info')
        parser.add_argument('--csv', '-c', action='store_true', help='Format output as CSV')

    def add_subparser(self, subparsers):
        parser = self._setup_subparser(subparsers)
        self._add_arguments(parser)

    def print_line(self, key, value, pad=20):
        if not value:
            return None
        if isinstance(value, list):
            value = ', '.join(value)
        key += ':'
        print key.ljust(pad, ' '), value

    def run(self, args):
        for name in args.items:
            obj = clusto.get(name)
            if not obj:
                sys.stderr.write('Object does not exist: %s\n' % name)
                continue
            obj = obj[0]

            for label, key in PROPERTY_MAP:
                value = getattr(obj, key, None)
                self.print_line(label, value)

            #sys.stdout.write('\n')

            self.print_line('Parents', [x.name for x in obj.parents()])
            self.print_line('Contents', [x.name for x in obj.contents()])
            
            sys.stdout.write('\n')

            self.print_line('IP', obj.attr_values(key='ip', subkey='ipstring'))
            self.print_line('Public DNS', obj.attr_values(key='ec2', subkey='public-dns'))
            self.print_line('Private DNS', obj.attr_values(key='ec2', subkey='private-dns'))

            sys.stdout.write('\n')

            self.print_line('Owner', ['%s: %s' % (x.subkey, x.value) for x in obj.attrs(key='owner')])
            self.print_line('Serial',
                [x.rstrip('\r\n') for x in obj.attr_values(
                key='system', subkey='serial')])

            memory = obj.attr_value(key='system', subkey='memory')
            if memory:
                self.print_line('Memory', '%i GB' % (int(memory) / 1000))

            disk = obj.attr_value(key='system', subkey='disk')
            if disk:
                self.print_line('Disk', '%i GB (%i)' % (int(disk),
                len([int(x) for x in obj.attr_values(key='disk', subkey='size')])))

            cpucount = obj.attr_value(key='system', subkey='cpucount')
            if cpucount:
                self.print_line('CPU Cores', int(cpucount))

            self.print_line('Description', obj.attr_values(key='description'))
            sys.stdout.write('\n')

            if len(args.items) > 1:
                sys.stdout.write(('-' * 40) + '\n\n')


def main():
    info, args = script_helper.init_arguments(Info)
    return(info.run(args))

if __name__ == '__main__':
    sys.exit(main())

