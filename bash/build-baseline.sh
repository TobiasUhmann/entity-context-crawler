#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-baseline \
  data/irt.fb.irt/ \
  baseline-irt-fb-irt \
  --output-dir 'data/' \
> log/build-baseline_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
