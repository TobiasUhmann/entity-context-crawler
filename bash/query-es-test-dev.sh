#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py query-es-test \
  cw-contexts-v7-2020-12-31 \
  data/ow-contexts-v7-2020-12-31.db \
  --limit-entities 10 \
  --random-seed 0 \
> log/query-es-test-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
