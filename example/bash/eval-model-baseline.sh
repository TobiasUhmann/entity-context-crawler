#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py eval-model \
  baseline \
  data/irt.fb.irt.30.clean/ \
  --baseline-dir 'data/baseline-v1-irt-fb-irt-30-clean/' \
  --baseline-name baseline-v1-irt-fb-irt-30-clean \
> log/eval-model-baseline_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
