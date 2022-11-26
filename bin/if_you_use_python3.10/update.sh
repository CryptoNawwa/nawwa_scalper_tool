#!/bin/bash
source ../_common/_update.sh

## run install
python3.10 setup.py install --user

sleep 0.2
printf "\n\n"
echo "Update done with python3 ! Press enter to quit :) "
read enter
