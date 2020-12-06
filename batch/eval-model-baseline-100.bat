set PYTHONPATH=src\
python -u src\sam.py eval-model ^
  baseline ^
  data\oke.fb15k237_30061990_50\ ^
  --baseline-es-index cw-contexts-v7-enwiki-20200920-100-500 ^
  --baseline-ow-db data/ow-contexts-v7-enwiki-20200920-100-500.db
