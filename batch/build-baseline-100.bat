set PYTHONPATH=src\
python -u src\sam.py build-baseline ^
  data\oke.fb15k237_26041992_100_masked\ ^
  baseline-v1-26041992-100-masked ^
  --limit-contexts 100 ^
  --output-dir 'data\'
