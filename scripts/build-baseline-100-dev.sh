#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py build-baseline \
  data/enwiki-20200920-contexts-100-500.db \
  data/oke.fb15k237_30061990_50/ \
  enwiki-20200920-cw-contexts-100-500-dev \
  data/enwiki-20200920-ow-contexts-100-500-dev.db \
  --limit-contexts 100 \
  --overwrite \
  --random-seed 0 \
> log/build-baseline-100-dev_$(date +"%Y-%m-%d_%H-%M-%S").stdout &
