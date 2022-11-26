#!/bin/bash

path_bybit_api_keys_base=terminal/exchanges/bybit/api_keys.json.base
path_bybit_api_keys=terminal/exchanges/bybit/api_keys.json

printf "\nHello ~ ~ :D \n\n"

cd ..
cd ..

sleep 0.2
echo "Enter your Bybit API_KEY:"
read bybit_api_key
sleep 0.2
printf "\nEnter your Bybit API_SECRET:\n"
read bybit_api_secret
echo '
{
    "BybitApiKey": "'$bybit_api_key'",
    "BybitSecretApiSecret": "'$bybit_api_secret'"
}' > $path_bybit_api_keys
printf "Done\n\n" 


sleep 0.2
echo "Running python install command.."
sleep 0.5
