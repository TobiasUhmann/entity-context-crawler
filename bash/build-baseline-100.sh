#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-baseline \
  data/oke.fb15k237_26041992_100/ \
  baseline-100-oke.fb15k237_26041992_100 \
  --limit-contexts 100 \
  --output-dir 'data/' \
> log/build-baseline-100_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
