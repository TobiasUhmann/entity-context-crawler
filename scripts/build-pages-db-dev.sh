#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py build-pages-db \
  data/enwiki-2018-09-text.xml \
  data/pages-v1-enwiki-2018-09-text-dev.db \
  --limit-pages 1000 \
  --overwrite \
  --random-seed 0 \
> log/build-pages-db-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
