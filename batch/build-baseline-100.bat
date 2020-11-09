set PYTHONPATH=src\
python -u src\sam.py build-baseline ^
  data\contexts-v6-enwiki-20200920-100-500.db ^
  data\oke.fb15k237_30061990_50\ ^
  cw-contexts-v6-enwiki-20200920-100-500 ^
  data\ow-contexts-v6-enwiki-20200920-100-500.db ^
  --limit-contexts 100
