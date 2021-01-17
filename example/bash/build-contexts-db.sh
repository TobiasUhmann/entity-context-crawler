#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-contexts-db \
  data/wikidata-codex.json \
  data/qid2rid-codex.txt \
  data/matches-codex.db \
  data/contexts-codex.db \
  --context-size 500 \
  --crop-sentences \
  --csv-file data/contexts-codex.csv \
  --limit-contexts 100 \
> log/build-contexts-db_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
