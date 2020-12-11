#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py eval-model \
  baseline \
  data/oke.fb15k237_26041992_100_clean/ \
  --baseline-dir 'data/' \
  --baseline-name baseline-v1-26041992-100-masked \
  --random-seed 0 \
> log/eval-model-baseline-masked-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
