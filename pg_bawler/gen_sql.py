#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate trigger function and installation sql statements.

For most basic usage you need only name of the table you
want to be notified on changes.

    $ python -m pg_bawler.gen_sql mytable

And pg_bawler will generate plpgsql function code and
create trigger statements. Thus installation should be
easy as:

    $ python -m pg_bawler.gen_sql mytable | psql mydb
"""
import argparse
import sys

import jinja2


TRIGGER_FUNCTION_TEMPLATE = 'trigger.sql.tpl'
DROP_TRIGGER_TEMPLATE = 'drop_trigger.sql.tpl'
CREATE_TRIGGER_TEMPLATE = 'create_trigger.sql.tpl'

TRIGGER_FN_FMT = 'bawler_trigger_fn_{args.tablename}'
TRIGGER_NAME_FMT = 'bawler_trigger_{args.tablename}'


def get_default_cli_args_parser():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        'tablename',
        metavar='TABLENAME', type=str,
        help='Name of sql table you want ot generate trigger code for.')
    parser.add_argument(
        '--channel',
        metavar='CHANNEL', type=str,
        help='Notify / Listen channel name.')
    parser.add_argument(
        '--trigger',
        metavar='TRIGGER_NAME', type=str,
        help='Generated trigger name.')
    parser.add_argument(
        '--trigger-fn',
        metavar='TRIGGER_FUNCTION_NAME', type=str,
        help='Generated trigger function name.')
    parser.add_argument(
        '--no-drop',
        action='store_true',
        help='Do not generate DROP TRIGGER sql statement.')
    parser.add_argument(
        '--no-create',
        action='store_true',
        help='Do not generate CREATE TRIGGER sql statement.')
    parser.add_argument(
        '--only-drop',
        action='store_true',
        help='Generate only DROP TRIGGER sql statement.')
    parser.add_argument(
        '--only-create',
        action='store_true',
        help='Generate only CREATE TRIGGER sql statement.')
    return parser


def get_default_tpl_loader():
    return jinja2.Environment(
        loader=jinja2.PackageLoader(__package__, 'templates'))


def _get_and_render_template(context, tpl_loader, tpl_name):
    tpl_loader = tpl_loader or get_default_tpl_loader()
    return tpl_loader.get_template(tpl_name).render(**context)


def get_trigger_function_code(
    context,
    tpl_loader=None,
    tpl_name=TRIGGER_FUNCTION_TEMPLATE
):
    return _get_and_render_template(context, tpl_loader, tpl_name)


def get_drop_trigger_statement(
    context,
    tpl_loader=None,
    tpl_name=DROP_TRIGGER_TEMPLATE
):
    return _get_and_render_template(context, tpl_loader, tpl_name)


def get_create_trigger_statement(
    context,
    tpl_loader=None,
    tpl_name=CREATE_TRIGGER_TEMPLATE
):
    return _get_and_render_template(context, tpl_loader, tpl_name)


def create_context_from_args(args):
    return {
        'table_name': args.tablename,
        'channel': args.channel or args.tablename,
        'trigger_fn_name': args.trigger_fn or TRIGGER_FN_FMT.format(args=args),
        'trigger_name': args.trigger or TRIGGER_NAME_FMT.format(args=args),
    }


def main():
    args = get_default_cli_args_parser().parse_args()
    tpl_loader = get_default_tpl_loader()
    context = create_context_from_args(args)

    if not (args.only_drop or args.only_create):
        sys.stdout.write(get_trigger_function_code(context, tpl_loader))
    if not (args.no_drop or args.only_create):
        sys.stdout.write(get_drop_trigger_statement(context, tpl_loader))
    if not (args.no_create or args.only_drop):
        sys.stdout.write(get_create_trigger_statement(context, tpl_loader))


if __name__ == '__main__':
    sys.exit(main())
