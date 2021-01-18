#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py build-contexts-db \
  data/wikidata-codex.json \
  data/qid2rid-codex.txt \
  data/matches-codex.db \
  data/contexts-codex-dev.db \
  --context-size 500 \
  --crop-sentences \
  --csv-file data/contexts-codex-dev.csv \
  --limit-contexts 100 \
  --limit-entities 10 \
  --overwrite \
  --random-seed 0 \
> log/build-contexts-db-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
