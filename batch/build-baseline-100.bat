set PYTHONPATH=src\
python -u src\sam.py build-baseline ^
  data\oke.fb15k237_30061990_50\ ^
  baseline-100-oke.fb15k237_26041992_100 ^
  --limit-contexts 100 ^
  --output-dir 'data\oke.fb15k237_30061990_50\'
