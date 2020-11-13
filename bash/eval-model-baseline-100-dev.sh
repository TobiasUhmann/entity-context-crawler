#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py eval-model \
  data/oke.fb15k237_30061990_50/ \
  cw-contexts-v7-enwiki-20200920-100-500 \
  data/ow-contexts-v7-enwiki-20200920-100-500.db \
  --limit-entities 100 \
  --model baseline-100 \
  --random-seed 0 \
> log/eval-model-baseline-100-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
