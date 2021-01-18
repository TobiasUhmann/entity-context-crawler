set PYTHONPATH=src\
set PYTHONHASHSEED=0
python -u src\sam.py eval-model ^
  baseline ^
  data\irt.fb.irt.30.clean\ ^
  --baseline-dir 'data\baseline-v1-irt-fb-irt-30-clean\' ^
  --baseline-name baseline-v1-irt-fb-irt-30-clean
  --random-seed 0
