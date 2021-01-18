#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py eval-model \
  baseline \
  data/irt.fb.irt/ \
  --baseline-dir 'data/baseline-irt-fb-irt/' \
  --baseline-name baseline-irt-fb-irt \
  --random-seed 0 \
> log/eval-model-baseline-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
