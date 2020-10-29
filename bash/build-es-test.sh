#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-es-test \
  data/contexts-v3-enwiki-20200920-100-500.db \
  cw-contexts-v3-enwiki-20200920-100-500 \
  data/ow-contexts-v3-enwiki-20200920-100-500.db \
  --limit-contexts 100 \
> log/build-es-test_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
