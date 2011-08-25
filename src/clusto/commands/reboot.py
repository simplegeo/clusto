#!/usr/bin/env python
# -*- mode: python; sh-basic-offset: 4; indent-tabs-mode: nil; coding: utf-8 -*-
# vim: tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8

import argparse
import sys

import clusto
from clusto import drivers
from clusto import script_helper

class Reboot(script_helper.Script):
    '''
    This will reboot a given server or IP address
    '''

    def __init__(self):
        script_helper.Script.__init__(self)

    def _add_arguments(self, parser):
        parser.add_argument('object', nargs=1,
            help='Entity name, IP, or MAC address')

    def add_subparser(self, subparsers):
        parser = self._setup_subparser(subparsers)
        self._add_arguments(parser)

    def run(self, args):
        try:
            obj = clusto.get(args.object[0])
        except Exception as e:
            self.debug(e)
            self.error('"%s" does not exist' % args.object[0])
            return -1
        obj = obj[0]
        if not hasattr(obj, 'reboot'):
            self.error('"%s" does not have a reboot() method.')
            return 1
        self.debug('Rebooting %s' % obj)
        print 'Parents: %s' % ' '.join([ _.name for _ in obj.parents() ])
        sys.stdout.write('Are you sure you want to reboot %s (yes/no)? ' % args.object[0])
        sys.stdout.flush()

        try:
            line = sys.stdin.readline().rstrip('\r\n')
        except KeyboardInterrupt:
            line = False

        if line != 'yes':
            print 'Aborting'
            return
        else:
            obj.reboot(captcha=False)
            print '%s is rebooting now.' % obj.name
        return


def main():
    reboot = Reboot()
    parent_parser = script_helper.setup_base_parser()
    this_parser = argparse.ArgumentParser(parents=[parent_parser],
        description=reboot._get_description())
    reboot._add_arguments(this_parser)
    args = this_parser.parse_args()
    reboot.init_script(args=args, logger=script_helper.get_logger(args.loglevel))
    return(reboot.run(args))


if __name__ == '__main__':
    sys.exit(main())

