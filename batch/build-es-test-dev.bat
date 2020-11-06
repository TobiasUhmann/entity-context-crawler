set PYTHONPATH=src\
set PYTHONHASHSEED=0
python -u src\sam.py build-es-test ^
  data\contexts-v6-enwiki-20200920-100-500.db ^
  cw-contexts-v6-enwiki-20200920-100-500-dev ^
  data\ow-contexts-v6-enwiki-20200920-100-500-dev.db ^
  --limit-contexts 100 ^
  --overwrite ^
  --random-seed 0
