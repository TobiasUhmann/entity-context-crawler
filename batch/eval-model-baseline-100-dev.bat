set PYTHONPATH=src\
set PYTHONHASHSEED=0
python -u src\sam.py eval-model ^
  data\oke.fb15k237_30061990_50\ ^
  cw-contexts-v7-enwiki-20200920-100-500 ^
  data\ow-contexts-v7-enwiki-20200920-100-500.db ^
  --limit-entities 100 ^
  --model baseline-100 ^
  --random-seed 0
