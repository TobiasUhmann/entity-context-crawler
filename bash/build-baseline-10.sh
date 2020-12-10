#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-baseline \
  data/oke.fb15k237_26041992_100/ \
  baseline-10-oke.fb15k237_26041992_100 \
  --limit-contexts 10 \
  --output-dir 'data/' \
> log/build-baseline-10_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
