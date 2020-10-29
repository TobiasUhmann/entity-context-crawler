set PYTHONPATH=src\
python -u src\sam.py build-es-test ^
  data\contexts-v3-enwiki-20200920-100-500.db ^
  cw-contexts-v3-enwiki-20200920-100-500-qa ^
  data\ow-contexts-v3-enwiki-20200920-100-500-qa.db ^
  --limit-contexts 100
