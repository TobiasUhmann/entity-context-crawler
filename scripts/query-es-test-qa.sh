#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py query-es-test \
  cw-contexts-v1-enwiki-20200920-100-500 \
  data/ow-contexts-v1-enwiki-20200920-100-500.db \
  --limit-entities 10 \
> log/query-es-test-qa_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
