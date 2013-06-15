#! -*- coding: utf-8 -*-

from nose.tools import *
from argtools import Command, argument


def test_command_usage():
    command = Command()
    run_tracks = []

    @command
    def main(args):
        """ Here is used as description

        Write details (show in epilog).
        """
        run_tracks.append({
            'file': args.file,
            'test': args.test,
            'verbose': args.verbose,
        })

    # setup arguments and run
    command.add_arg('file')
    command.add_arg('-t', '--test', action='store_true', default=False)
    command.run(args=['foo.txt', '-v'])
    eq_(run_tracks.pop(), {'file': 'foo.txt', 'test': False, 'verbose': 1})

    # you can also run with decorated 'main'
    main.run(args=['--test', 'bar.txt', '-vv'])
    eq_(run_tracks.pop(), {'file': 'bar.txt', 'test': True, 'verbose': 2})


def test_subcommand_usage():
    command = Command()
    run_tracks = []

    # create common argument
    common1 = argument()
    common1.add_arg('file', help='this is common option')
    common1.add_arg(argument('--some-flag', action='store_true'))

    # setup subcommand "main1" (basic style)
    sub = command.add_sub()
    sub.add_arg(common1)
    sub.add_arg('-t', '--test', action='store_true', default=False)

    @sub
    def sub1(args):
        """ This line is used as description

        Write details (show in epilog).
        """
        run_tracks.append({
            'file': args.file,
            'test': args.test,
            'verbose': args.verbose,
            'some_flag': args.some_flag,
        })


    # setup subcommand "sub2" (decorator style)

    @command.add_sub
    @argument(common1)
    @argument('-t', '--times', action='count', default=0)
    def sub2(args):
        """ This line is used as description

        Write details here (show in epilog).
        """
        run_tracks.append({
            'file': args.file,
            'times': args.times,
            'verbose': args.verbose,
            'some_flag': args.some_flag,
        })


    # with group, exclusive

    @command.add_sub
    @argument('-a')
    @argument.group(
       'Counting options',
       'Description of counting options',
       argument('-c', '--counts', action='count', default=0),
       argument('-t', '--times', action='count', default=0),
    )
    @argument.exclusive(
       argument('--tsv', action='store_const', const='tsv', dest='filetype'),
       argument('--csv', action='store_const', const='csv', dest='filetype'),
       required=True,
    )
    def sub3(args):
        """ This line is used as description

        Write details here (show in epilog).
        """
        run_tracks.append({
            'a': args.a,
            'counts': args.counts,
            'times': args.times,
            'filetype': args.filetype,
        })


    # root command option
    #command.add_arg('--detail', help='this is root only option')

    # run sub1
    command.run(args=['sub1', 'foo.txt', '-t'])
    eq_(run_tracks.pop(), {'file': 'foo.txt', 'test': True, 'verbose': 0, 'some_flag': False})

    # run sub2
    #command.run(args=['sub2', 'bar.txt', '-t', '--times', '-v'])
    command.run(args=['sub2', 'bar.txt', '-t', '--times', '--some-flag'])
    eq_(run_tracks.pop(), {'file': 'bar.txt', 'times': 2, 'verbose': 0, 'some_flag': True})

    # run sub3
    #command.run(args=['sub2', 'bar.txt', '-t', '--times', '-v'])
    command.run(args=['sub3', '-t', '--times', '-cc', '--counts', '--csv'])
    eq_(run_tracks.pop(), {'times': 2, 'counts': 3, 'a': None, 'filetype': 'csv'})

    # run subcommand directly
    sub1.run(args=['foo.txt', '-t', '-v', '--some-flag'])
    eq_(run_tracks.pop(), {'file': 'foo.txt', 'test': True, 'verbose': 1, 'some_flag': True})
