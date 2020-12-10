#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py build-baseline \
  data/oke.fb15k237_26041992_100/ \
  baseline-10-dev-oke.fb15k237_26041992_100 \
  --limit-contexts 10 \
  --output-dir 'data/' \
  --overwrite \
  --random-seed 0 \
> log/build-baseline-10-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
