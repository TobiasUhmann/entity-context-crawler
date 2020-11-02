#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py eval-model \
  data/oke.fb15k237_30061990_50/ \
  data/ow-contexts-v4-enwiki-20200920-10-500.db \
  --model baseline-10 \
  --random-seed 0 \
> log/eval-model-baseline-10-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
