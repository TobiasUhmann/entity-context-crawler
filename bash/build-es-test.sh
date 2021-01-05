#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-es-test \
  data/contexts-v7-2020-12-31.db \
  cw-contexts-v7-2020-12-31 \
  data/ow-contexts-v7-2020-12-31.db \
  --limit-contexts 100 \
> log/build-es-test_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
