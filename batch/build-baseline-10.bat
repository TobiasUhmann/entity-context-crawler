set PYTHONPATH=src\
python -u src\sam.py build-baseline ^
  data\oke.fb15k237_30061990_50\ ^
  data\contexts-v7-enwiki-20200920-100-500.db ^
  cw-contexts-v7-enwiki-20200920-10-500 ^
  data\ow-contexts-v7-enwiki-20200920-10-500.db ^
  data\baseline-v1-enwiki-20200920-10-500.p ^
  --limit-contexts 10
