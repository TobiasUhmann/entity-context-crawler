#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-pages-db \
  data/enwiki-20200920.xml \
  data/enwiki-2018-09-text.xml \
  data/pages-v2-enwiki-20200920-enwiki-2018-09-qa.db \
> log/build-pages-db-qa_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
