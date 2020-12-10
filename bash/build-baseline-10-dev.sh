#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py build-baseline \
  data/oke.fb15k237_30061990_50/ \
  baseline-10-dev-oke.fb15k237_26041992_100 \
  --limit-contexts 10 \
  --output-dir 'data/oke.fb15k237_30061990_50/' \
  --overwrite \
  --random-seed 0 \
> log/build-baseline-10-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
