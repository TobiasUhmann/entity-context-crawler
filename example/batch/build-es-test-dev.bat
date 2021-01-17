set PYTHONPATH=src\
set PYTHONHASHSEED=0
python -u src\sam.py build-es-test ^
  data\contexts-v7-2020-12-31.db ^
  cw-contexts-v7-2020-12-31-dev ^
  data\ow-contexts-v7-2020-12-31-dev.db ^
  --limit-contexts 100 ^
  --overwrite ^
  --random-seed 0
