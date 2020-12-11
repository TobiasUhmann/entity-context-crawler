#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py eval-model \
  baseline \
  data/oke.fb15k237_26041992_100_clean/ \
  --baseline-dir 'data/baseline-v1-26041992-100-clean/' \
  --baseline-name baseline-v1-26041992-100-clean \
  --random-seed 0 \
> log/eval-model-baseline-clean-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
