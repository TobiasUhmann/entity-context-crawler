#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-pages-db \
  data/enwiki-2018-09-text.xml \
  data/pages-v1-enwiki-2018-09-text.db \
  --in-memory \
> log/build-pages-db_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
