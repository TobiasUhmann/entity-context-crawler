#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py build-contexts-db \
  data/matches-v1-enwiki-20200920.db \
  data/contexts-v1-enwiki-20200920-100-500-dev.db \
  --context-size 500 \
  --crop-sentences \
  --csv-file data/contexts-v1-enwiki-20200920-100-500-dev.csv \
  --limit-contexts 100 \
  --limit-entities 10 \
  --overwrite \
  --random-seed 0 \
> log/build-contexts-db-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
