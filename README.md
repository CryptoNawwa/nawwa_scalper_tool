# A Bybit Scalper Tool

# Wat
I built this little piece of code so we can finally do like the big boys on binance and exit our 0.2 ETH position with 2 scale orders ! 

Incredible

It's my first time building something in python so please don't insult me on twitter, there is probably 100 better ways to organize the code and I'm sure it could be more efficient, but it works so heh


## Features

- scale order (reduce only, used as TP)
- cool UI
- shortcut

Shortcuts :
Open the shortcuts.json file under data/ and modify it 
Scale order syntax --> scale [nb of order] [from_%] to [to_%]

## Available commands
---
Switch the active ticker to ETHUSDT

```sh
ticker ethusdt
t ethusdt
```
---
Will create 10 limit order (reduce only) to exit the current position on the active ticker, from 0.1 above entry_price to 0.4 above entry price (or below if short)

```sh
scale 10 0.1 to 0.2
sc 10 0.1 to 0.2
```
---
## Tech

I used a number of open source projects to make it work properly:

- [Textual] - TUI plugin, based on Rich
- [Pybit] - Bybit python connector
- [Baywatch] - I just copy pasted the config part, I put him here to give credit
- [TextualListView] - Custom Texual widget list
- [TextInput] - Custom Text input widget


## Installation

Requires Python3

Install the dependencies

```sh
pip3 install textual
pip install textual-inputs~=0.2.6
pip3 install git+https://github.com/Cvaniak/TextualListViewUnofficial.git 
pip3 install pybit
```

To launch config UI (so you can put your api keys):

```sh
python3 app.py -c
```

To launch the actual app UI :

```sh
python3 app.py
```
## General info
Use it a your own risk, it's a random piece a code made by a stranger on the internet, by downloading this you take full responsibility, if you download this and lose money it's on you.

## Next

- cancel all limit orders 
- automatically setup scale TP orders when we enter a position, based on cfg
- ..


## License

MIT


   [Textual]: <https://github.com/Textualize/textual>
   [PyBit]: <https://github.com/bybit-exchange/pybit>
   [BayWatch]: <https://github.com/hdb/baywatch>
   [TextualListView]: <https://github.com/Cvaniak/TextualListViewUnofficial>
   [TextInput]: <https://github.com/sirfuzzalot/textual-inputs>
