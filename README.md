argtools
==========

Description
-------------------
Just a wrapper of argparse module which is included in Python standard libraries for ver. >= 2.7.
Argtools helps you to build command line tools with *minimal effort*.

Quick start
-------------------

### Installation
```sh
$ pip install argtools
```

### Basic usage

```python
# examples/test.py
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
```

```sh
$ python test.py
$ python test.py -v   # It setups logging module internally and has verbose mode
```

The argument function has same api as argparse.ArgumentParser.add_argument.
(see http://docs.python.org/dev/library/argparse.html for detail.)


### Creating subcommands

```python
# examples/subtest.py
from argtools import command, argument

@command.add_sub
def foo(args):
    """ This is foo
    """
    print 'foo'


@command.add_sub
def bar(args):
    """ This is bar
    """
    print 'bar'


@command.add_sub(name=baz)  # set different name
def bar(args):
    """ This is baz
    """
    print 'baz'

if __name__ == '__main__':
    command.run()
```

```sh
$ python test.py foo      # print foo
$ python test.py bar      # print bar
$ python test.py bar -h   # print help text of bar subcommand
```


Features
-------------------

- command.run setups logging module internally and can control verbosity like -v, -vv, ..
- command.run ignores SIGPIPE occured inside of wrapped function
- It supports group or exclusive arguments by argument.group, argument.exclusive (documentation is #TODO)
- Builtin options (-v, --verbose, --debug) can be turned off by setting command.add_verbose = False or command.add_debug = False
