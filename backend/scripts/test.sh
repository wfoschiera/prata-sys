#!/usr/bin/env bash

set -e
set -x

coverage run -m pytest -n auto tests/
coverage report
# Remove htmlcov/ before regenerating — it may be owned by root if previously
# generated inside a Docker container, causing PermissionError.
rm -rf htmlcov/
coverage html --title "${@-coverage}"
