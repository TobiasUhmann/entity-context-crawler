#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-baseline \
  data/oke.fb15k237_26041992_100_masked/ \
  baseline-v1-26041992-100-masked \
  --output-dir 'data/' \
> log/build-baseline-masked_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
