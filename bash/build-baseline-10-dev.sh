#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py build-baseline \
  data/contexts-v2-enwiki-20200920-100-500.db \
  data/oke.fb15k237_30061990_50/ \
  cw-contexts-v2-enwiki-20200920-10-500-dev \
  data/ow-contexts-v2-enwiki-20200920-10-500-dev.db \
  --limit-contexts 10 \
  --overwrite \
  --random-seed 0 \
> log/build-baseline-10-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
