#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-pages-db \
  data/enwiki-2018-09-text.xml \
  data/enwiki-2018-09-text-qa.db \
  --in-memory \
> log/build-pages-db-qa_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
