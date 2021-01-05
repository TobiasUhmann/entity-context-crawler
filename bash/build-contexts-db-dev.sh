#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py build-contexts-db \
  data/wikidata-v1-2020-12-31.json \
  data/qid-to-rid-v1-2020-12-31.txt \
  data/matches-v5-enwiki-20200920.db \
  data/contexts-v7-enwiki-20200920-100-500-dev.db \
  --context-size 500 \
  --crop-sentences \
  --csv-file data/contexts-v7-enwiki-20200920-100-500-dev.csv \
  --limit-contexts 100 \
  --limit-entities 10 \
  --overwrite \
  --random-seed 0 \
> log/build-contexts-db-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
