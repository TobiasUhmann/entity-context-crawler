set PYTHONPATH=src\
python -u src\sam.py build-baseline ^
  data\oke.fb15k237_26041992_100\ ^
  baseline-10-oke.fb15k237_26041992_100 ^
  --limit-contexts 10 ^
  --output-dir 'data\'
