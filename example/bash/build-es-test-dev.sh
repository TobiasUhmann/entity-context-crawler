#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py build-es-test \
  data/contexts-v8-codex.db \
  cw-contexts-v8-codex-dev \
  data/ow-contexts-v8-codex-dev.db \
  --limit-contexts 100 \
  --overwrite \
  --random-seed 0 \
> log/build-es-test-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
