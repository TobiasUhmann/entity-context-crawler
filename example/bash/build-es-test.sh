#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-es-test \
  data/contexts-v8-codex.db \
  cw-contexts-v8-codex \
  data/ow-contexts-v8-codex.db \
  --limit-contexts 100 \
> log/build-es-test_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
