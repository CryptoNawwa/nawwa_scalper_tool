#!/bin/bash
source ../_common/_update.sh

## run install
python setup.py install --user

sleep 0.2
printf "\n\n"
echo "Update done with python ! Press enter to quit :) "
read enter
