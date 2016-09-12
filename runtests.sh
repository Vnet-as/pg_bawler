#!/bin/sh

# pip install -Ue .
pre-commit run --all-files && python -m pytest
