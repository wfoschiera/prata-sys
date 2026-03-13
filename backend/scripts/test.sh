#!/usr/bin/env bash

set -e
set -x

coverage run -m pytest tests/
coverage report
coverage html --title "${@-coverage}" || echo "⚠️  coverage html failed (possibly permissions on htmlcov/)" >&2
