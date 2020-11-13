#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py eval-model \
  data/oke.fb15k237_30061990_50/ \
  cw-contexts-v7-enwiki-20200920-100-500 \
  data/ow-contexts-v7-enwiki-20200920-100-500.db \
  --model baseline-100 \
> log/eval-model-baseline-100_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
