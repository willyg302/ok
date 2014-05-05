# strap.py

---

A simple tool for cloning, copying, and initializing Python projects, because bootstrapping shouldn't be so gosh-durn hard.

## Install

Clone this repo and put the `strap/` directory somewhere convenient (for this readme, we will assume the user's home directory). It's also immensely helpful to alias `python ~/strap` to something like `strap`.

## Usage

`strap <uri-or-path-to-repo> [path-to-output-dir]`

Examples:

```bash
strap ../somedir/otherdir/strap-this
strap copy/this ../to/here/and-then-strap-it
strap https://github.com/willyg302/Parrot
strap gh:willyg302/jarvis
strap git@github.com:willyg302/jarvis.git ~/jarvis-test
```

You can also use it programmatically, if that's your cup of tea:

### strap.json

## Why?

I found myself writing the same old code for every Python project to automate its installation. Conventional programmer's logic states that if you do it more than once, it should become a tool.