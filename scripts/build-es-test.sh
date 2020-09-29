#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-es-test \
  data/enwiki-20200920-contexts-100-500.db \
  enwiki-20200920-cw-contexts-100-500 \
  data/enwiki-20200920-ow-contexts-100-500.db \
  --limit-contexts 100 \
> log/build-es-test_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
