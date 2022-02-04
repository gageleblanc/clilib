#!/bin/bash

rm -r dist/
python3 setup.py bdist_wheel
docker build .
