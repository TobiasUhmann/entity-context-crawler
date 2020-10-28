#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-es-test \
  data/contexts-v2-enwiki-20200920-100-500.db \
  cw-contexts-v2-enwiki-20200920-100-500-qa \
  data/ow-contexts-v2-enwiki-20200920-100-500-qa.db \
  --limit-contexts 100 \
> log/build-es-test-qa_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
