#!/bin/bash
source ../_common/_update.sh

## run install
py setup.py install --user

sleep 0.2
printf "\n\n"
echo "Update done with py ! Press enter to quit :) "
read enter
