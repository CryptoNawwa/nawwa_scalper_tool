#!/bin/bash
source ../_common/_install.sh

sleep 0.2
echo "Running py install command.."
sleep 0.5
py setup.py install --user

if [ $? -eq 0 ]; then
   echo "Installation was successful !"
   echo "Press enter to quit !"
   read enter
   exit 0 
else
    echo "Installation failed :("
    echo "Take a screenshot and contact me on discord -> Nawwa#8129 \n"
    echo "Press enter to quit !"
    read enter
    exit 1 
fi
