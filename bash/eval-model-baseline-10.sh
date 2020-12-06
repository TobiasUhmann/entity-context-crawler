#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py eval-model \
  baseline-10 \
  data/oke.fb15k237_30061990_50/ \
  --baseline-es-index cw-contexts-v7-enwiki-20200920-10-500 \
  --baseline-ow-db data/ow-contexts-v7-enwiki-20200920-10-500.db \
> log/eval-model-baseline-10_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
