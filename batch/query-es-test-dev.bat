set PYTHONPATH=src\
set PYTHONHASHSEED=0
python -u src\sam.py query-es-test ^
  cw-contexts-v4-enwiki-20200920-100-500 ^
  data\ow-contexts-v4-enwiki-20200920-100-500.db ^
  --limit-entities 10 ^
  --random-seed 0
