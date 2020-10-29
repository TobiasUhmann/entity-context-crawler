#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py eval-model \
  data/oke.fb15k237_30061990_50/ \
  data/ow-contexts-v3-enwiki-20200920-100-500.db \
  --model baseline-100 \
> log/eval-model-baseline-100-qa_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
