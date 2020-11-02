set PYTHONPATH=src\
python -u src\sam.py query-es-test ^
  cw-contexts-v5-enwiki-20200920-100-500 ^
  data\ow-contexts-v5-enwiki-20200920-100-500.db ^
  --limit-entities 10
