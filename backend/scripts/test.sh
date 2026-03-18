#!/usr/bin/env bash

set -e
set -x

# pytest-cov handles xdist workers natively — no need for coverage run + combine
pytest -n auto \
  --cov=app \
  --cov-context=test \
  --cov-report=term-missing:skip-covered \
  --cov-report=html \
  tests/
