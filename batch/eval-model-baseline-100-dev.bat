set PYTHONPATH=src\
set PYTHONHASHSEED=0
python -u src\sam.py eval-model ^
  baseline-100 ^
  data\oke.fb15k237_30061990_50\ ^
  data\ow-contexts-v7-enwiki-20200920-100-500.db ^
  --baseline-cw-es-index cw-contexts-v7-enwiki-20200920-100-500 ^
  --limit-entities 100 ^
  --random-seed 0
