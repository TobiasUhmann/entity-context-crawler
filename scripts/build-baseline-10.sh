#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-baseline \
  data/enwiki-20200920-contexts-100-500.db \
  data/oke.fb15k237_30061990_50/ \
  enwiki-20200920-cw-contexts-10-500 \
  data/enwiki-20200920-ow-contexts-10-500.db \
  --limit-contexts 10 \
> log/build-baseline-10_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
