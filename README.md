![strap.py](https://raw.github.com/willyg302/strap.py/master/strap-logo.png "There's a snake in mah boot!")

---

strap is Make for stupid people: a simple tool for cloning, copying, and initializing projects, because bootstrapping shouldn't be so gosh-durn hard. Inspired by [init-skeleton](https://github.com/paulmillr/init-skeleton).

## Install

Clone this repo and put the `strap/` directory somewhere convenient (for this readme, we will assume the user's home directory). It's also immensely helpful to alias `python ~/strap` to something like `strap`.

## Usage

```bash
strap
strap [-h, --help] [--version] {init,run,cache} ...
```

Calling `strap` without any arguments is equivalent to `strap run default`.

> **Note**: It may be necessary to `sudo` to elevate privileges, as strap installs necessary tools globally if they are not present. If you are using strap via an alias, don't forget to add `alias sudo='sudo '` to your shell's profile.

### init

`strap init [-h, --help] [-d, --dest DEST] [-s, --silent] source`

`source` can either be a directory or a GitHub repo URI. `DEST` is an optional directory. If `DEST` is given, then `source` will be cloned or copied into it. If `DEST` is omitted, then `source` will either be cloned into the current working directory (if it is a URI) or "refreshed" (if it is a directory, the equivalent of `strap run install`).

**Examples**:

```bash
strap init ../somedir/otherdir/strap-this
strap init copy/this --dest ../to/here/and-then-strap-it
strap init -s https://github.com/willyg302/Parrot
strap init gh:willyg302/jarvis
strap init git@github.com:willyg302/jarvis.git -d ~/jarvis-test
```

### run

`strap run [-h, --help] [-d, --dir DIR] [-s, --silent] [tasks [tasks ...]]`

You can provide a list of one or more `tasks` to run. If given, `DIR` specifies the path to execute tasks from; it defaults to the current working directory. Note that calling `strap run` (no arguments) is equivalent to `strap run default`.

**Examples**:

```bash
strap
strap run sometask --silent
strap run task_a task_b also_do_this --dir from/this/directory
```

### cache

`strap cache [-h, --help] {clean,list}`

Use this command to manage strap's dependency cache. You can `list` currently known modules (including ones that have failed to install) and `clean` the cache to start anew.

### list

`strap list [-h, --help]`

List the available tasks defined in a project's `strapme.py`. By convention, functions beginning with an underscore are ignored.

### strapme.py

Once a project is fetched with `strap init`, it will be installed according to the rules defined in `strapme.py` located at its root directory.

```python
import os

project = 'My Optional Project Name'

def print_cwd():
    print('Hello from {}!'.format(os.getcwd()))

def task_name():
    '''The optional name of this task'''
    with strap.root('subdirectory-of-project/to-run-task-in'):
        with strap.virtualenv('virtual-environment-name'):
            strap.run([
                'pip install some-module',
                'easy_install this-other-module'
            ])
            strap.freeze('requirements.txt')

def shell():
    strap.run([
        'echo Oh yeah I can run other stuff too!',
        'npm install'
    ])

def python():
    '''Call a Python function? No problem.'''
    with strap.root('../lets-do-it-here'):
        print_cwd()  # Or strap.run(print_cwd)

def install():
    strap.run([task_name, shell, python])

def default():
    strap.run(install)
```

Essentially, each function defined in `strapme.py` is a task. The "install" and "default" tasks are required; without them, you'll probably get errors. Note that you can do anything in `strapme.py` that you would normally do in a Python script, including importing needed modules, but it is best to stick with standard or globally-installed modules.

#### Metadata

- Define a global variable `project` to give your project a name
- Name a task using its function docstring

#### API

strap exposes the `strap` variable for use in tasks. This variable has the following standard functions:

Function       | Description
-------------- | -----------
`root()`       | Pass a path to a directory to carry out the task in. Use with the `with` statement.
`freeze()`     | Pass the name of a file to `pip freeze` into. Only really useful within a virtual environment.
`ping()`       | "Ping" a shell command, returning `True` if the process exits with code 0.
`run()`        | Either a single subtask or a list of subtasks to run. Each subtask may either be a Python function or a string that will be interpreted as a shell command. Returns `self` for chaining.

The following modules are also defined:

Module         | Returns `self` | Description
-------------- | -------------- | -----------
`bower`        | Yes            | Call any regular bower command. Pass an optional `root` kwarg to define the directory to execute bower in.
`easy_install` | Yes            | Call any regular easy_install command.
`make`         | Yes            | Call any regular make command, or no command to simply run Make.
`node`         | Yes            | Call any regular node command. Pass the `module=True` kwarg to identify the command as a Node module (e.g. `gulp`) to be run locally.
`npm`          | Yes            | Call any regular npm command.
`pip`          | Yes            | Call any regular pip command.
`virtualenv`   | No             | Pass the name of a virtual environment to execute in. If it does not exist, it will be created. Use with the `with` statement.

### From Code

You can also use strap programmatically, if that's your cup of tea:

**COMING SOON**

## Why?

I found myself writing the same old code for every project to automate its installation. Conventional programmer's logic states that if you do it more than once, it should become a tool.

## Roadmap (v0.4.0)

- [x] Clean up and refactor existing code to be more modular
- [x] Add Node/NPM modules
- [ ] Basic tests
- [ ] Programmatic functionality and documentation
