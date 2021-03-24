#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py build-contexts-db \
  data/wikidata-v1-codex.json \
  data/qid-to-rid-v1-codex.txt \
  data/matches-v6-codex.db \
  data/contexts-v8-codex-dev.db \
  --context-size 500 \
  --crop-sentences \
  --csv-file data/contexts-v8-codex-dev.csv \
  --limit-contexts 100 \
  --limit-entities 10 \
  --overwrite \
  --random-seed 0 \
> log/build-contexts-db-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &