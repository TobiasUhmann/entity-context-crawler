set PYTHONPATH=src\
python -u src\sam.py build-es-test ^
  data\contexts-v7-enwiki-20200920-100-500.db ^
  cw-contexts-v7-enwiki-20200920-100-500 ^
  data\ow-contexts-v7-enwiki-20200920-100-500.db ^
  --limit-contexts 100
