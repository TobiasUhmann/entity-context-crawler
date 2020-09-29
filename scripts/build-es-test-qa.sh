#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-es-test \
  data/enwiki-20200920-contexts-100-500.db \
  enwiki-20200920-cw-contexts-100-500-qa \
  data/enwiki-20200920-ow-contexts-100-500-qa.db \
  --limit-contexts 100 \
> log/build-es-test-qa_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
