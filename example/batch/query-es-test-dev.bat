set PYTHONPATH=src\
set PYTHONHASHSEED=0
python -u src\sam.py query-es-test ^
  cw-contexts-v7-2020-12-31 ^
  data\ow-contexts-v7-2020-12-31.db ^
  --limit-entities 10 ^
  --random-seed 0
