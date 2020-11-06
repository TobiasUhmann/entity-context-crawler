set PYTHONPATH=src\
set PYTHONHASHSEED=0
python -u src\sam.py eval-model ^
  data\oke.fb15k237_30061990_50\ ^
  data\ow-contexts-v5-enwiki-20200920-100-500.db ^
  --model baseline-100 ^
  --random-seed 0
