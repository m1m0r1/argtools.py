#!/usr/bin/env python
from argtools import command, argument


@command
@argument('foo', help='a positional arugment')
@argument('--bar', default=3, help='an optional argument')
def main(args):
    """ One line description here

    Write details here (printed with --help|-h)
    """
    print args.bar
    print args.foo
    return 1  # return code


if __name__ == '__main__':
    command.run()
