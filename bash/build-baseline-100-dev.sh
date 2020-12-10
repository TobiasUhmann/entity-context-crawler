#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py build-baseline \
  data/oke.fb15k237_26041992_100/ \
  baseline-100-dev-oke.fb15k237_26041992_100 \
  --limit-contexts 100 \
  --output-dir 'data/' \
  --overwrite \
  --random-seed 0 \
> log/build-baseline-100-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
