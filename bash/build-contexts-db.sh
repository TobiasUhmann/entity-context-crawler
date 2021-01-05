#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-contexts-db \
  data/wikidata-v1-2020-12-31.json \
  data/qid-to-rid-v1-2020-12-31.txt \
  data/matches-v6-2020-12-31.db \
  data/contexts-v7-2020-12-31.db \
  --context-size 500 \
  --crop-sentences \
  --csv-file data/contexts-v7-2020-12-31.csv \
  --limit-contexts 100 \
> log/build-contexts-db_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
