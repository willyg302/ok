# strap.py

---

A simple tool for cloning, copying, and initializing Python projects, because bootstrapping shouldn't be so gosh-durn hard. Inspired by [init-skeleton](https://github.com/paulmillr/init-skeleton).

## Install

Clone this repo and put the `strap/` directory somewhere convenient (for this readme, we will assume the user's home directory). It's also immensely helpful to alias `python ~/strap` to something like `strap`.

## Usage

`strap <source> [dest]`

`source` can either be a directory or a GitHub repo URI. `dest` is an optional directory. If `dest` is given, then `source` will be cloned or copied into it. If `dest` is omitted, then `source` will either be cloned into the current working directory (if it is a URI) or "refreshed" (if it is a directory).

Examples:

```bash
strap ../somedir/otherdir/strap-this
strap copy/this ../to/here/and-then-strap-it
strap https://github.com/willyg302/Parrot
strap gh:willyg302/jarvis
strap git@github.com:willyg302/jarvis.git ~/jarvis-test
```

You can also use it programmatically, if that's your cup of tea:

**COMING SOON**

### strap.json

Once a project is fetched, it will be installed according to the rules defined in `strap.json` located at its root directory.

```json
{
    "project": "My Project Name",
    "tasks": [
        {
            "name": "The optional name of this task",
            "root": "subdirectory-of-project/to-run-task-in",
            "virtualenv": "virtual-environment-name",
            "requirements": [
                "pip install some-module",
                "easy_install this-other-module"
            ],
            "freeze": "requirements.txt"
        },
        {
            "name": "Oh yeah I can run other stuff too!",
            "requirements": ["npm install"]
        }
    ]
}
```

Tasks are run sequentially and fully separate from each other. With the exception of the `requirements` array, all task properties are optional. If a `virtualenv` is given, then the `requirements` will be installed into the virtual environment.

## Why?

I found myself writing the same old code for every Python project to automate its installation. Conventional programmer's logic states that if you do it more than once, it should become a tool.