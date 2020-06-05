#!/bin/bash

PYTHONUNBUFFERED=1 \
PYTHONHASHSEED=0 \
python ../src/link-extractor.py "$@"
