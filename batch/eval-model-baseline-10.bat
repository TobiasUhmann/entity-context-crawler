set PYTHONPATH=src\
python -u src\sam.py eval-model ^
  data\oke.fb15k237_30061990_50\ ^
  data\ow-contexts-v4-enwiki-20200920-10-500.db ^
  --model baseline-10
