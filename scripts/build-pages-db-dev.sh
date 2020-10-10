#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-pages-db \
  data/enwiki-20200920.xml \
  data/pages-v1-enwiki-20200920-dev.db \
  --limit-pages 1000 \
  --overwrite \
  --random-seed 0 \
> log/build-pages-db-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
