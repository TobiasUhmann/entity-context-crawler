set PYTHONPATH=src\
set PYTHONHASHSEED=0
python -u src\sam.py build-baseline ^
  data\oke.fb15k237_30061990_50\ ^
  baseline-10-dev-oke.fb15k237_26041992_100 ^
  data\contexts-v7-enwiki-20200920-100-500.db ^
  cw-contexts-v7-enwiki-20200920-10-500-dev ^
  data\ow-contexts-v7-enwiki-20200920-10-500-dev.db ^
  data\baseline-v1-enwiki-20200920-10-500-dev.p ^
  --limit-contexts 10 ^
  --output-dir 'data\oke.fb15k237_30061990_50\' ^
  --overwrite ^
  --random-seed 0
