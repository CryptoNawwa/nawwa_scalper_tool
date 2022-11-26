#!/bin/bash
now=$(date '+%H-%M-%S')


## go back in path 
cd ..

sleep 0.2
printf "\n"
echo "Saving folders name..."
sleep 0.5

## save name master folder
name_master_folder=${PWD##*/}
echo ${name_master_folder}

## go back in path again
cd ..

new_code_source_folder_name=nawwa_scalper_tool-${now}

prev_path_bybit_api_keys=$name_master_folder/terminal/exchanges/bybit/api_keys.json
prev_path_shortuts=$name_master_folder/terminal/shortcuts/shortcuts.json

new_path_bybit_api_keys=${new_code_source_folder_name}/terminal/exchanges/bybit/api_keys.json
new_path_shortuts=${new_code_source_folder_name}/terminal/shortcuts/shortcuts.json

sleep 0.2
printf "\n"
echo "Copying shortcuts and api keys.."
sleep 0.5
## copy shortcuts and api keys
cp $prev_path_bybit_api_keys .
cp $prev_path_shortuts .

sleep 0.2
printf "\n"
echo "Downloading new source code.."
## get source code
until curl -LJO "https://github.com/CryptoNawwa/nawwa_scalper_tool/archive/refs/heads/main.zip"
do
  sleep 5
done

sleep 0.2
printf "\n"
echo "Unziping source code..."
sleep 0.5
## unzip source code
unzip nawwa_scalper_tool-main
rm nawwa_scalper_tool-main.zip

## rename new code
mv nawwa_scalper_tool-main ${new_code_source_folder_name}

sleep 0.2
echo "Copying shortcuts and api keys into new source code..."
sleep 0.5
## copy shortcuts in new code source
cp shortcuts.json $new_path_shortuts 
## copy api_keys in new code source
cp api_keys.json $new_path_bybit_api_keys

rm shortcuts.json
rm api_keys.json

## go into new code source folder
cd ${new_code_source_folder_name}

## run install
python3 setup.py install --user

sleep 0.2
printf "\n\n"
echo "Update done ! Press enter to quit :) "
read enter


