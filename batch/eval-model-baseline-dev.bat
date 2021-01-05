set PYTHONPATH=src\
set PYTHONHASHSEED=0
python -u src\sam.py eval-model ^
  baseline ^
  data\irt.fb.30.26041992.clean\ ^
  --baseline-dir 'data\baseline-v1-irt-fb-30-26041992-clean\' ^
  --baseline-name baseline-v1-irt-fb-30-26041992-clean
  --random-seed 0