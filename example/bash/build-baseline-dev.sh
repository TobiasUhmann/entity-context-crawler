#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py build-baseline \
  data/irt.fb.irt/ \
  baseline-irt-fb-irt-dev \
  --output-dir 'data/' \
  --overwrite \
  --random-seed 0 \
> log/build-baseline-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
