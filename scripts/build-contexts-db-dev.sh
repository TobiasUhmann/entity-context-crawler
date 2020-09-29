#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py build-contexts-db \
  data/enwiki-20200920-matches.db \
  data/enwiki-20200920-contexts-100-500-dev.db \
  --context-size 500 \
  --crop-sentences \
  --csv-file data/enwiki-20200920-contexts-100-500-dev.csv \
  --limit-contexts 100 \
  --limit-entities 10 \
  --overwrite \
  --random-seed 0 \
> log/build-contexts-db-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
