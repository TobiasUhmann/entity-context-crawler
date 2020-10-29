#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py query-es-test \
  cw-contexts-v2-enwiki-20200920-100-500 \
  data/ow-contexts-v2-enwiki-20200920-100-500.db \
  --limit-entities 10 \
  --random-seed 0 \
> log/query-es-test-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
