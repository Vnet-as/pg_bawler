#!/bin/sh

pip install -Ue .
watchmedo shell-command \
	--recursive \
	--patterns='*.py;*.tpl' \
	--drop \
	--command='/bin/sh runtests.sh' \
	.
