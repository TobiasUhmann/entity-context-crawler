#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-es-test \
  data/contexts-codex.db \
  cw-contexts-codex \
  data/ow-contexts-codex.db \
  --limit-contexts 100 \
> log/build-es-test_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
