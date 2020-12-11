set PYTHONPATH=src\
python -u src\sam.py build-baseline ^
  data\oke.fb15k237_26041992_100\ ^
  baseline-v1-26041992-10 ^
  --limit-contexts 10 ^
  --output-dir 'data\'
