#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py eval-model \
  baseline-100 \
  data/oke.fb15k237_30061990_50/ \
  data/ow-contexts-v7-enwiki-20200920-100-500.db \
  --baseline-cw-es-index cw-contexts-v7-enwiki-20200920-100-500 \
  --random-seed 0 \
> log/eval-model-baseline-100-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
