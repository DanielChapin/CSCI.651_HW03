#!/bin/bash
source venv/bin/activate && cd src && python3 -m demos.$1 "${@:2}"