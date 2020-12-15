#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py build-baseline \
  data/oke.fb15k237_26041992_100_clean/ \
  baseline-v1-26041992-100-clean-dev \
  --output-dir 'data/' \
  --overwrite \
  --random-seed 0 \
> log/build-baseline-clean-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
