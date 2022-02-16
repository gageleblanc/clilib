#!/bin/bash

if [ -d "./html" ]; then
    source cleanup.sh
fi

pdoc3 clilib -c show_source_code=False --html -o html
docker build -t gleblanc/clilib-docs:latest .
docker push gleblanc/clilib-docs:latest
