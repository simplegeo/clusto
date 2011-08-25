#!/usr/bin/env python
# -*- mode: python; sh-basic-offset: 4; indent-tabs-mode: nil; coding: utf-8 -*-
# vim: tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8

import argparse
import sys

import clusto
from clusto import drivers
from clusto import script_helper


class InitDB(script_helper.Script):
    '''
    Operate on a pool or on its objects. You can create, delete or show
    a pool and you can insert or remove items to/from a pool
    '''

    def __init__(self):
        script_helper.Script.__init__(self)

    def run(self, args):
        clusto.init_clusto()

def main():
    initdb, args = script_helper.init_arguments(InitDB)
    return(initdb.run(args))

if __name__ == '__main__':
    sys.exit(main())

