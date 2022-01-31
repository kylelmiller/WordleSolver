# Wordle Solver

Uses Monte Carlo to solve any Wordle puzzle with a 100% success rate. To see it work run `simulategames.py`. 
If you want to use it to help with an unknown Wordle puzzle use `unknownwordle.py`. 

## Requirements

* Python 3.8

## Known Issues

The dictionary is a subset of the Wordle dictionary. I looked around for a list of 5 letter English words and a lot of
them had "words" that were not words. I went with a safe list where every word was a real English word at the cost of
missing words.
