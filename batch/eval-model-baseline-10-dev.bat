set PYTHONPATH=src\
set PYTHONHASHSEED=0
python -u src\sam.py eval-model ^
  data\oke.fb15k237_30061990_50\ ^
  data\ow-contexts-v7-enwiki-20200920-10-500.db ^
  --model baseline-10 ^
  --random-seed 0
