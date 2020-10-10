#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-pages-db \
  data/enwiki-20200920.xml \
  data/pages-v1-enwiki-20200920-qa.db \
> log/build-pages-db-qa_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
