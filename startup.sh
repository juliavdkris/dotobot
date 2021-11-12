#!/bin/bash

find storage-override/ -maxdepth 1 -mindepth 1 -type d -not -name 'db' -exec cp -r {} storage/ \;
python src/main.py
