#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py build-es-test \
  data/contexts-v5-enwiki-20200920-100-500.db \
  cw-contexts-v5-enwiki-20200920-100-500-dev \
  data/ow-contexts-v5-enwiki-20200920-100-500-dev.db \
  --limit-contexts 100 \
  --overwrite \
  --random-seed 0 \
> log/build-es-test-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
