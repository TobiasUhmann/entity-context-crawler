#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py query-es-test \
  cw-contexts-codex \
  data/ow-contexts-codex.db \
  --limit-entities 10 \
> log/query-es-test_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
