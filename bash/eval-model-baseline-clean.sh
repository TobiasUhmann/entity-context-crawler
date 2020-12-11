#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py eval-model \
  baseline \
  data/oke.fb15k237_26041992_100_clean/ \
  --baseline-dir 'data/' \
  --baseline-name baseline-v1-26041992-100-clean \
> log/eval-model-baseline-clean_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
