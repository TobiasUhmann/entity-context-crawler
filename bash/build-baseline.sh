#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-baseline \
  data/irt.fb.30.26041992.clean/ \
  baseline-v1-irt-fb-30-26041992-clean \
  --output-dir 'data/' \
> log/build-baseline_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
