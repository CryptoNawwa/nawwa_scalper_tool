
# Nawwa Scalper Tool

This CLI is a textual UI (TUI) scalping tool, it's goal is to automate certain action when you are trading / scalping, aka : place scale orders, auto-limit order, cancel orders, shortcuts..  

This `tool` was made because our friend [Ichibot](https://gitlab.com/Ichimikichiki/ichibot-client-app) does not support Bybit yet !  

The current version of the NawwaBot only support the **Bybit** exchange but the code was made in a way that's easy for any developer to implement a new exchange
# Demo

Smol demo 
[![asciicast](https://asciinema.org/a/gXh5ocBOkqe3e5L5JvR59bdUn.svg)](https://asciinema.org/a/gXh5ocBOkqe3e5L5JvR59bdUn)

# How to update

If you already have a version of this bot running you just have to download the new source code.

It will download a folder on your computer, just navigate to the folder and run the bot like you are use to.    

You just have to keep 2 files :  

- shortcut.json (where you store your aliases and shortcuts)
- conf.json (where you store your api keys)


---

Keep your current bot folder just in case the new version is not working for you so you can still go back and use the bot located in your current folder.


Shoot me a message on discord if you have any problem <3

# How to install

**MacOS / LINUX**  
Use any terminal you want

**Windows**  
Because it's a graphic UI, you will need to use a specific terminal called [Windows Terminal](https://apps.microsoft.com/store/detail/windows-terminal/9N0DX20HK701?hl=fr-fr&gl=fr). It's a terminal developed by microsoft and you can install it using the microsoft store. Do that first.

### Installation guide 
Install this  :

- [Python 3.10](https://www.python.org/downloads/release/python-3105/) (Scroll at bottom & download)


You are ready, follow the steps :

Download the project using this link, then unzip it

```bash
  https://github.com/CryptoNawwa/nawwa_scalper_tool/archive/refs/heads/main.zip
```

Open your terminal and navigate to the project directory

```bash
  cd nawwa_scalper_tool
```

Install dependencies

```bash
  pip3 install textual~=0.1.18
  pip3 install textual-inputs~=0.2.6
  pip3 install ck-widgets==0.2.0
  pip3 install pybit~=2.4.0
  pip3 install install rich~=12.5.1
```

Go into app folder

```bash
  cd app
```

Open the `bybit/data/conf.json` file using any text editor and copy past your apy keys so it look like this :  
```json
{
    "BybitApiKey": "my_apy_key_here",
    "BybitSecretApiSecret": "my_secret_api_here"
}
```

If you are inside the `App` folder,  Run the bot using this command :

```bash
  python3 frontend.py
```

You are done, you can use the bot !


# Features

- Cool UI kekW
- Display current active ticker in terminal UI 
- Display current position size in terminal UI
- Place scale reduce-only limit orders based on .% range (only support reduce-only order atm)
- Place only 1 (one) reduce only limit order, based on .% away from entry
- Automatic take-profit system, it will automatically place pre-configured scale orders when you enter any position
- Cancel all orders
- Create/Update/Delete your Shortcuts (shortcuts = alias for your commands)


# Shortcuts

To add / remove shortcuts, open the `shortcuts.json` file located in `app/shortcuts/shortcuts.json` and modify it to your needs.

Shortcut file syntax is :
```json
{
    "name_of_shortcut" : "command",
    "name_of_shortcut_2" : "command"
}
```

Example of a shortcut file : 
```json
{
    "s1": "scale 5 0.01 0.03", 
    "s2": "scale 5 0.02 0.04",

    "tp1": "tp 0.1",
    "tp4": "tp 0.3",

    "atp4": "atp ON tp4",
    "atp4": "atp ON s1",

    "atom" : "ticker atomusdt",
    "eth" : "ticker ethusdt",
    "etc" : "ticker etcusdt" 
}
```

Pretty simple, when you type ```tp1``` in the terminal, it will execute `scale 5 0.01 0.03`

You can press `L` on the UI and it will display the shortcut list, press `L` again to close

*Note : Shortcut are also used by the `autotp` command.*
# Command list


### **ticker [ticker_name]**


This command switch the active ticker to a new one
```sh
ticker ethusdt
or 
t ethusdt
```
In this example, the command set the active ticker to `ETHUSDT`

The current active ticker is displayed on your terminal, above user input

*Note : You will need to have a ticker selected to execute certain command*


---

### **scale [nb_of_order] [from_%] [to_%]**

This command create `[nb_of_order]` reduce-only limit order(s) on the active ticker, from `[from_%]` above entry_price to `[to_%]` above entry price (or below if short)
```sh
scale 10 0.1 to 0.2
or
s 10 0.1 to 0.2
```
In this example,  it will create 10 orders from 0.1% to 0.2%

*Note : For this command to work you need to have an open position on the active ticker*

---

### **tp [away_from_entry_%]**

This command create 1 (one) reduce-only limit order on the active ticker, from `[away_from_entry_%]` above entry_price (or below if short)
```sh
tp 0.4
```
In this example,  it will create 1 order from 0.4% away from entry price

*Note : For this command to work you need to have an open position on the active ticker*


---
### **cancel [type_of_cancel]**

This command cancel limit orders for the current ticker, based on the type

Available types: 
- all


```sh
cancel all
or
c all
```

---
### **shortcut [action] [shortcut_name] [shortcut_value]**

This command will do the `[atp_action]` with `[shortcut_name]` and `[shortcut_value]` as parameter  

This command is usefull to add / remove / modify shortcuts

Available actions: 
- ADD
- UPDATE (UP)
- DEL


```sh
shortcut ADD tp10 scale 4 0.5 0.9
or
s ADD tp10 scale 4 0.5 0.9`
```
In this example, a shortcut named `tp10` will be added to the `shortcuts.json` file, with the shortcut value being `scale 4 0.5 0.9`

Assuming the file was empty, after this command it will look like this :   

```json
{
    "tp10": "scale 4 0.5 0.9", 
}
```

Now, when you type `tp10` in the terminal, it will execute `scale 4 0.5 0.9`

### **UPDATE** example
```sh
autotp UP tp10 scale 2 0.1 0.2
or
atp UP tp10 scale 2 0.1 0.2
```
The `update` action is usefull when you want to update a certain shortcut to do something else

The result of this example in the `shortcuts.json` file is :

```json
{
    "tp10": "scale 2 0.1 0.2", 
}
```
### **DELETE** example
```sh
autotp DEL tp10 
or
atp DEL tp10
```
The `del` action will delete the shortcut

The result of this example in the `shortcuts.json` file is :

```json
{
    // nothing is here since you deleted it kekLMAO
}
```


---
### **autotp [atp_action] [shortcut_name] (cancel_off)**

This command will perform the `[atp_action]` with `[shortcut_name]` as parameter, `cancel_off` is optional

Actions availabe : 
- ON
- OFF
- UPDATE
- STATUS

Writing `cancel_off` at the end will disable the automatic cancelation of orders when the ATP is triggered.    


Autotp (for automatic take profit) system will automatically set reduce-only limit orders based on the shortcut config you gave him.  

:warning: Once it's `ON` , the `autotp` system works for all the positions you enter, on every ticker. It means that if you take a trade on another pair, it will place the limit order(s), it's not only related to the current active ticker (might change that later if it's a problem)

### **ON** examples
```sh
autotp ON tp1
or
atp ON tp1
```
This will activate the autotp system with the shortcut `tp1` as limit order config  
It means, if we enter a position on any coin, the bot will execute this shortcut `"tp1" : scale 10 0.1 to 0.2 ` 

- It will cancel the limit orders active for this coin (if any)  
- It will automatically set 10 limit orders from 0.1 to 0.2 each time you enter a position

*Note : Obviously, only use `scale` or `tp` shortcuts*
```sh
atp ON tp1 cancel_off
```
This will activate the autotp system with the shortcut `tp1` as limit order config, with the `cancel_off` options.  

It means, if we enter a position on any coin, the bot will execute this shortcut `"tp1" : scale 10 0.1 to 0.2 `

- It will **NOT** cancel the limit orders active for this coin  
- It will automatically set 10 limit orders from 0.1 to 0.2 each time you enter a position

### **UPDATE** example
```sh
autotp UPDATE tp4 
or
atp UP tp4
or 
atp UP tp4 cancel_off
```
This will update the shortcut used by the `autotp` cmd to the shortcut called `tp4`

*Note : shortcuts needs to be defined in the file located in shortcuts/shortcuts.json*

### **OFF** example
```sh
autotp OFF
or
atp OFF
```
This will disable the `autotp` system

### **STATUS** example
```sh
autotp STATUS 
or
atp ST
```
This will print the current status (ON / FF)


# For devs - How to Implement another exchange 

The code was made so it's easy for any developer to implement another exchange than Bybit (hopefully)

You just have to create a class that implements the `Exchange` abstract class, and the methods.



Then, for the frontend to use your exchange, just replace the `exchange_client` parameter in `frontend.py` :
```python
    Frontend.run(exchange_client=Bybit(), title="Nawwa's Scalping Tool", log="scalping_tool.log")

```
by 

```python
    Frontend.run(exchange_client=YOUR_EXCHANGE_CLASS_HERE(), title="Nawwa's Scalping Tool", log="scalping_tool.log")

```

Everything is typed with `TypedDict`, so as long as you return the correct data, it should work



# Support

If you need any help, follow & dm me on twitter [crypto_nawwa](https://twitter.com/crypto_nawwa) or add me on Discord: Nawwa#8129

# Disclaimer 

Downloading and using this bot is at your own risk, you take full responsabilities and if you lose money it's your own fault. I recommand using it on a test account first.


# License

[MIT](https://choosealicense.com/licenses/mit/)

