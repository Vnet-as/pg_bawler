#!/bin/sh

# pip install -Ue .
pre-commit run --all-files \
  && python -m pytest \
    -s \
    --exitfirst \
    --verbose \
    --pg-tag 9.6 \
    --cov pg_bawler \
    --cov-report term-missing \
    tests
