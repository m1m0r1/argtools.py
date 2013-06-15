# -*- coding: utf-8 -*-
""" A wrapper of argparse that helps to build command line tools with minimal effort.
"""

__author__ = "Takahiro Mimori <takahiro.mimori@gmail.com>"
__all__ = ['command', 'argument', 'Command', 'Error']

import os
import sys
import logging
import argparse
import textwrap
import functools

class Error(Exception):
    pass


class Command(object):
    """ Setup argparse and logging concicely and create decorator for function to invoke
    """

    logger = logging
    log_level = logging.WARNING
    log_format = "%(asctime)-15s [%(levelname)s] %(message)s"
    add_verbose = True
    add_debug = True
    formatter_class = argparse.RawDescriptionHelpFormatter

    def __init__(self):
        self._fn = None
        self._arg_stack = []
        self._children = []
        self.__doc__ = ''
        self.__name__ = ''
        self._before_runs = []

    def _take_over(self, target):
        """ Decorate self to behave like target object
        """
        assert callable(target)
        if target is self: # nothing to takeover
            return self

        if isinstance(target, Command):
            self._arg_stack.extend(target._arg_stack)
            self._fn = target._fn
        else:
            self._fn = target
        self.__doc__ = target.__doc__
        self.__name__ = target.__name__
        self.__module = target.__module__
        return self

    @property
    def description(self):
        line = (self.__doc__ or '').split('\n', 1)[0].lstrip()
        return line[:1].lower() + line[1:] # let first letter lower case

    @property
    def epilog(self):
        return textwrap.dedent('\n'.join((self.__doc__ or '').split('\n')[1:]))

    @property
    def name(self):
        return getattr(self, '__name__', None)

    def __call__(self, target=None): # dispatching
        if target is None:
            return self

        if callable(target): # wrap callable
            self._take_over(target)
            return self

        raise Error('Call this with empty or callable')

    def add_argument(self, *args, **kwds):
        """ Wrapper method for ArgumentParser.add_argument_group

        Typical usage:
            1) cmd.add_argument('-a', '--alpha')
            2) common = argument()
               common.add_argument('-a', '--alpha')
               common.add_argument('-b', '--beta')
               cmd.add_arguemnt(common, '-c', '--gamma')
        """
        # no argument to add to stack
        if not args:
            return self

        # consume Command objects if exists
        if isinstance(args[0], Command):
            self._arg_stack.extend(args[0]._arg_stack)
            target = args[0]
            return self.add_argument(*args[1:], **kwds)

        # stack args, kwds to pass to parser.add_argument
        self._arg_stack.append(('normal', args, kwds))
        return self

    add_arg = add_argument  # alias

    def add_group(self, *args, **kwds):
        """ Wrapper method for ArgumentParser.add_argument_group

        Typical usage:
            1) cmd.add_group(title, description, argument('-a'), argument('-b'))
            2) cmd.add_group(argument('-a'), argument('-b'), title=title, description=description)
        """
        title = kwds.pop('title', None)
        description = kwds.pop('description', None)
        if kwds:
            raise Exception('unknown keyword arguments: %s' % kwds)

        # set title, description if args[0] is string
        if isinstance(args[0], (str, unicode)):
            title = args[0]
            args = args[1:]
            if isinstance(args[0], (str, unicode)):
                description = args[0]
                args = args[1:]

        assert all(isinstance(arg, Command) for arg in args), 'all args should be instance of Command'
        self._arg_stack.append(('group', args, {'title': title, 'description': description}))
        return self

    def add_exclusive(self, *args, **kwds):
        """ Wrapper method for ArgumentParser.add_mutually_exclusive_group

        Typical usage:
            1) cmd.add_exclusive(argument('--tsv', action='store_const', const='tsv', dest='filetype'),
                                 argument('--csv', action='store_const', const='csv', dest='filetype'),
                                 required=True)
        """
        required = kwds.pop('required', False)
        if kwds:
            raise Exception('unknown keyword arguments: %s' % kwds)

        assert all(isinstance(arg, Command) for arg in args), 'all args should be instance of Command'
        self._arg_stack.append(('exclusive', args, {'required': required}))
        return self

    def add_sub(self, *targets):
        """ Add callable as subcommand

        Typical usage:
            @command.add_sub
            @argument('file')
            def process(args):
                print args.file
        """
        new = self.__class__()

        for target in targets:
            if not callable(target):
                raise Error('Call this with empty or callable')
            new._take_over(target)

        self._children.append(new)
        return new

    def _add_parser_rules(self, parser):
        if self.add_verbose:
            parser.add_argument('-v', '--verbose', action='count', default=0, help='increase verbosity level')
        if self.add_debug:
            parser.add_argument('--debug', action='store_true', default=False, help='debug mode')

        for (arg_type, args, kwds) in self._arg_stack:
            if arg_type == 'normal':
                parser.add_argument(*args, **kwds)
            elif arg_type == 'group':
                group = parser.add_argument_group(title=kwds['title'], description=kwds['description'])
                for arg in args:
                    for (_, _args, _kwds) in arg._arg_stack:
                        group.add_argument(*_args, **_kwds)
            elif arg_type == 'exclusive':
                group = parser.add_mutually_exclusive_group(required=kwds['required'])
                for arg in args:
                    for (_, _args, _kwds) in arg._arg_stack:
                        group.add_argument(*_args, **_kwds)
            else:
                raise Error('unknown argument type: %s' % arg_type)

        if self._fn:
            parser.set_defaults(func=self._fn)

    def before_run(self, fn):
        self._before_runs.append(fn)
        return fn

    def run(self, args=None):
        parser = argparse.ArgumentParser(description=self.description,
                                         epilog=self.epilog,
                                         formatter_class=self.formatter_class)
        # setup root parser
        self._add_parser_rules(parser)

        # setup subcommand parsers
        if self._children:
            subs = parser.add_subparsers(help='valid subcommands')
            for subcmd in self._children:
                if subcmd.name is None:
                    continue # skip trailing subcommand
                subp = subs.add_parser(subcmd.name,
                                       description=subcmd.description,
                                       epilog=subcmd.epilog,
                                       help=subcmd.description,
                                       formatter_class=self.formatter_class)
                subcmd._add_parser_rules(subp)

        args = parser.parse_args(args=args)
        for before_run in self._before_runs:
            before_run(args)

        return self._run(args.func, args)

    def _run(self, fn, args):
        self._setup_logger(args)

        shortname = os.path.basename(sys.argv[0])
        self.logger.info('start %s', shortname)
        try:
            return fn(args)
        except IOError, e:
            if e.errno != 32:  # ignore SIGPIPE
                raise
        finally:
            self.logger.info('end %s', shortname)

    def _setup_logger(self, args):
        verbosity = getattr(args, 'verbose', 0)
        if getattr(args, 'debug', False):
            verbosity = max(2, verbosity)  # set verbosity lower bound for debug mode

        log_level = max(self.log_level - verbosity * 10, 0)
        self.logger.basicConfig(format=self.log_format, level=log_level, stream=sys.stderr)


# decorators

command = Command()  # default command instance

def argument(*args, **kwds):
    return Command().add_argument(*args, **kwds)

argument.group = lambda *args, **kwds: Command().add_group(*args, **kwds)
argument.exclusive = lambda *args, **kwds: Command().add_exclusive(*args, **kwds)
