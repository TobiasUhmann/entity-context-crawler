#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-baseline \
  data/contexts-v1-enwiki-20200920-100-500.db \
  data/oke.fb15k237_30061990_50/ \
  cw-contexts-v1-enwiki-20200920-10-500-qa \
  data/ow-contexts-v1-enwiki-20200920-10-500-qa.db \
  --limit-contexts 10 \
> log/build-baseline-10_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
