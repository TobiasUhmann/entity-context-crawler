#!/bin/bash

PYTHONUNBUFFERED=1 \
PYTHONHASHSEED=0 \
python ../src/entity-matcher.py "$@"
