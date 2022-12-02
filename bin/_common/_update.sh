#!/bin/bash

# save now for folder names
now=$(date '+%H-%M-%S')

## go back to above root folder
cd ..
cd ..

sleep 0.2
printf "\n"
echo "Saving folders name..."
sleep 0.5

## save name of master folder
name_master_folder=${PWD##*/}
echo ${name_master_folder}

## go back in path again
cd ..

## store paths of new folder
new_code_source_folder_name=nawwa_scalper_tool-${now}
new_path_bybit_api_keys=${new_code_source_folder_name}/terminal/exchanges/bybit/api_keys.json
new_path_shortuts=${new_code_source_folder_name}/terminal/shortcuts/shortcuts.json

## store path of prev folder for api keys and shortcut
prev_path_bybit_api_keys=$name_master_folder/terminal/exchanges/bybit/api_keys.json
prev_path_shortuts=$name_master_folder/terminal/shortcuts/shortcuts.json


## store folder name of downloaded source code (match branch)
downloaded_folder_name=nawwa_scalper_tool-main
downloaded_folder_archive=${downloaded_folder_name}.zip

## store ource code download url
source_code_url=https://github.com/CryptoNawwa/nawwa_scalper_tool/archive/refs/heads/main.zip

sleep 0.2
printf "\n"
echo "Saving user shortcuts and api keys.."
sleep 0.5
cp $prev_path_bybit_api_keys .
cp $prev_path_shortuts .

sleep 0.2
printf "\n"
echo "Downloading new source code.."
until curl -LJO $source_code_url
do
  sleep 5
done


sleep 0.2
printf "\n"
echo "Unziping source code..."
sleep 0.5
mkdir update_tmp
unzip $downloaded_folder_name -d update_tmp/
rm $downloaded_folder_archive

## move new code folder to actual folder
mv update_tmp/${downloaded_folder_name} $new_code_source_folder_name
rm -rf update_tmp

sleep 0.2
echo "Copying shortcuts and api keys into new source code..."
sleep 0.5
cp shortcuts.json $new_path_shortuts
cp api_keys.json $new_path_bybit_api_keys

rm shortcuts.json
rm api_keys.json

## go into new code source folder so we can execute python install cmd
cd $new_code_source_folder_name


