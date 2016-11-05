#!/usr/bin/env python
import sys
from io import StringIO

from pg_bawler import gen_sql


def test_simple_main(monkeypatch):
    stdout = StringIO()
    monkeypatch.setattr(sys, 'stdout', stdout)

    class Args:
        tablename = 'foo'

    gen_sql.main(*[Args.tablename])
    sql = stdout.getvalue()

    assert gen_sql.TRIGGER_FN_FMT.format(args=Args) in sql
    assert gen_sql.TRIGGER_FN_FMT.format(args=Args) in sql


def test_no_drop(monkeypatch):
    stdout = StringIO()
    monkeypatch.setattr(sys, 'stdout', stdout)
    gen_sql.main('--no-drop', 'foo')
    sql = stdout.getvalue()
    assert 'DROP' not in sql
