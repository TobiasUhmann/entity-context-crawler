set PYTHONPATH=src\
set PYTHONHASHSEED=0
python -u src\sam.py build-baseline ^
  data\oke.fb15k237_30061990_50\ ^
  data\contexts-v7-enwiki-20200920-100-500.db ^
  cw-contexts-v7-enwiki-20200920-10-500-dev ^
  data\ow-contexts-v7-enwiki-20200920-10-500-dev.db ^
  --limit-contexts 10 ^
  --overwrite ^
  --random-seed 0
