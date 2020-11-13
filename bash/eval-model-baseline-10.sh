#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py eval-model \
  data/oke.fb15k237_30061990_50/ \
  cw-contexts-v7-enwiki-20200920-10-500 \
  data/ow-contexts-v7-enwiki-20200920-10-500.db \
  --model baseline-10 \
> log/eval-model-baseline-10_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
