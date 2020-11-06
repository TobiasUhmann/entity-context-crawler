set PYTHONPATH=src\
set PYTHONHASHSEED=0
python -u src\sam.py build-baseline ^
  data\contexts-v5-enwiki-20200920-100-500.db ^
  data\oke.fb15k237_30061990_50\ ^
  cw-contexts-v5-enwiki-20200920-10-500-dev ^
  data\ow-contexts-v5-enwiki-20200920-10-500-dev.db ^
  --limit-contexts 10 ^
  --overwrite ^
  --random-seed 0
