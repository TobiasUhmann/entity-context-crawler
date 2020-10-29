#!/bin/bash

PYTHONPATH=src/ \
nohup streamlit run src/app-launcher.py \
> log/app-launcher_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
