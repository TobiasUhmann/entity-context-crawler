#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-contexts-db \
  data/enwiki-20200920-matches.db \
  data/enwiki-20200920-contexts-100-500.db \
  --context-size 500 \
  --crop-sentences \
  --csv-file data/enwiki-20200920-contexts-100-500.csv \
  --limit-contexts 100 \
> log/build-contexts-db_$(date +"%Y-%m-%d_%H-%M-%S").stdout &
