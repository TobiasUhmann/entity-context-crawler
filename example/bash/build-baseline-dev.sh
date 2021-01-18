#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py build-baseline \
  data/irt.fb.irt.30.clean/ \
  baseline-v1-irt-fb-irt-30-clean-dev \
  --output-dir 'data/' \
  --overwrite \
  --random-seed 0 \
> log/build-baseline-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
