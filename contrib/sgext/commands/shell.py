#!/usr/bin/env python
# -*- mode: python; sh-basic-offset: 4; indent-tabs-mode: nil; coding: utf-8 -*-
# vim: tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8
#
# Shell command
# Copyright 2009, Ron Gorodetzky <ron@fflick.com>

import clusto
import sgext
from sgext.drivers import *
import clusto.commands.shell

def main():
    return clusto.commands.shell.main()

if __name__ == '__main__':
    sys.exit(main())
