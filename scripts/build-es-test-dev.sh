#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py build-es-test \
  data/enwiki-20200920-contexts-100-500.db \
  enwiki-20200920-cw-contexts-100-500-dev \
  data/enwiki-20200920-ow-contexts-100-500-dev.db \
  --limit-contexts 100 \
  --overwrite \
  --random-seed 0 \
> log/build-es-test-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
