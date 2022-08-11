#!/bin/bash

if [ -d "./html" ]; then
    source cleanup.sh
fi

pip3 install git+https://github.com/gageleblanc/pdoc-rest.git
pdoc clilib -c show_source_code=False --html -o html
docker build --no-cache -t gleblanc/clilib-docs:latest .
docker push gleblanc/clilib-docs:latest
