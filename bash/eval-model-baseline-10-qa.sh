#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py eval-model \
  data/oke.fb15k237_30061990_50/ \
  data/ow-contexts-v2-enwiki-20200920-10-500.db \
  --model baseline-10 \
> log/eval-model-baseline-10-qa_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
