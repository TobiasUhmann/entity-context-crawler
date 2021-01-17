#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py eval-model \
  baseline \
  data/irt.fb.irt/ \
  --baseline-dir 'data/baseline-irt-fb-irt/' \
  --baseline-name baseline-irt-fb-irt \
> log/eval-model-baseline_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
