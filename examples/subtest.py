#!/usr/bin/env python
from argtools import command, argument


@command.add_sub
def foo(args):
    """ This is bar
    """
    print 'foo'


@command.add_sub
def bar(args):
    """ This is bar
    """
    print 'bar'


if __name__ == '__main__':
    command.run()
