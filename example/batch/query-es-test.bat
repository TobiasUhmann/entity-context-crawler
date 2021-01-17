set PYTHONPATH=src\
python -u src\sam.py query-es-test ^
  cw-contexts-v7-2020-12-31 ^
  data\ow-contexts-v7-2020-12-31.db ^
  --limit-entities 10
