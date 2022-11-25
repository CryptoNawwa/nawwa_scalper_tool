#!/bin/bash

path_bybit_api_keys_copy=nawwa_scalper_tool/exchanges/bybit/api_keys.json.copy
path_bybit_api_keys=nawwa_scalper_tool/exchanges/bybit/api_keys.json

path_scalp_bybit=bin/scalp_bybit.sh
path_update=bin/update.sh

pyv="$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
pipv="$(pip3 --version)"

printf "\nHello ~ ~\n\nPress enter to start the install :D\n"
read enter

echo "Checking python3 & pip3 version..." 
sleep 0.5
if [[ -z "$pyv" ]]
then
    echo "Install failed" 
    echo "You do not have python3 installed.." 
    echo "Try to add python to the PATH of your terminal" 
    exit 0
fi

if [[ -z "$pipv" ]]
then
    echo "Install failed" 
    echo "You do not have python3 installed.." 
    echo "Try to add python to the PATH of your terminal" 
    exit 1
fi
printf "Done\n\n" 


cd ..
sleep 0.2
echo "Enter Bybit API_KEY:"
read bybit_api_key
sleep 0.2
printf "\nEnter Bybit API_SECRET:\n"
read bybit_api_secret
cp $path_bybit_api_keys_copy $path_bybit_api_keys
echo '
{
    "BybitApiKey": "'$bybit_api_key'",
    "BybitSecretApiSecret": "'$bybit_api_secret'"
}' > $path_bybit_api_keys
printf "Done\n\n" 

sleep 0.2
echo "Setting execution rights on scripts.."
sleep 0.5
chmod u+x $path_scalp_bybit
chmod u+x $path_update
ln -s $path_scalp_bybit shortcut_scalp_bybit
printf "Done\n"

sleep 0.2
echo "Running python install command.."
sleep 0.5
python3 setup.py install 
printf "\n\n"

if [ $? -eq 0 ]; then
   printf "Installation was successful !\n"
   echo "You can run scalp_bybit.sh to launch the terminal"
   echo "Press enter to quit !"
   read enter
   exit 0 
else
    printf "Installation failed :( \n"
    printf "Take a screenshot and contact me on discord -> Nawwa#8129 \n"
    echo "Press enter to quit !"
    read enter
    exit 1 
fi
