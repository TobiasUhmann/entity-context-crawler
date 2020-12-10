#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py build-baseline \
  data/oke.fb15k237_30061990_50/ \
  baseline-100-dev-oke.fb15k237_26041992_100 \
  data/contexts-v7-enwiki-20200920-100-500.db \
  cw-contexts-v7-enwiki-20200920-100-500-dev \
  data/ow-contexts-v7-enwiki-20200920-100-500-dev.db \
  data/baseline-v1-enwiki-20200920-100-500-dev.p \
  --limit-contexts 100 \
  --output-dir 'data/oke.fb15k237_30061990_50/' \
  --overwrite \
  --random-seed 0 \
> log/build-baseline-100-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
