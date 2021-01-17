#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-baseline \
  data/irt.fb.irt.30.clean/ \
  baseline-v1-irt-fb-irt-30-clean \
  --output-dir 'data/' \
> log/build-baseline_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
