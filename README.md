![strap.py](https://rawgit.com/willyg302/strap.py/master/strap-logo.svg "There's a snake in mah boot!")

---

A simple tool for cloning, copying, and initializing Python projects, because bootstrapping shouldn't be so gosh-durn hard. Inspired by [init-skeleton](https://github.com/paulmillr/init-skeleton).

## Install

Clone this repo and put the `strap/` directory somewhere convenient (for this readme, we will assume the user's home directory). It's also immensely helpful to alias `python ~/strap` to something like `strap`.

## Usage

```bash
strap
strap (--version)
strap <command> [<args>...]
```

Where `command` is one of `init` or `run`. Calling `strap` without any arguments is equivalent to `strap run default`.

> **Note**: All subcommands allow the `--verbose` flag, which is false by default to suppress the console spam that many installations generate. If you'd like to see all output, add this flag.

> **Note**: It may be necessary to `sudo` to elevate privileges, as strap.py installs necessary tools globally if they are not present. If you are using strap.py via an alias, don't forget to add `alias sudo='sudo '` to your shell's profile.

### init

`strap init [-v, --verbose] [-d, --dest=PATH] <source>`

`source` can either be a directory or a GitHub repo URI. `dest` is an optional directory. If `dest` is given, then `source` will be cloned or copied into it. If `dest` is omitted, then `source` will either be cloned into the current working directory (if it is a URI) or "refreshed" (if it is a directory, the equivalent of `strap run install`).

**Examples**:

```bash
strap init ../somedir/otherdir/strap-this
strap init copy/this --dest ../to/here/and-then-strap-it
strap init -v https://github.com/willyg302/Parrot
strap init gh:willyg302/jarvis
strap init git@github.com:willyg302/jarvis.git -d ~/jarvis-test
```

### run

`strap run [-v, --verbose] [-d, --dir=PATH] <task>...`

You can provide a list of one or more `task` to run. If given, `dir` specifies the path to execute tasks from; it defaults to the current working directory. Note that calling `strap` (no arguments) is equivalent to `strap run default` (but does not allow the `--verbose` flag).

**Examples**:

```bash
strap
strap run sometask --verbose
strap run task_a task_b also_do_this --dir from/this/directory
```

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

strap.py exposes the `strap` variable for use in tasks. This variable has the following functions:

Function       | Description
-------------- | -----------
`root()`       | Pass a path to a directory to carry out the task in. Use with the `with` statement.
`virtualenv()` | Pass the name of a virtual environment to execute in. If it does not exist, it will be created. Use with the `with` statement.
`shell()`      | Executes a shell command given as a string.
`freeze()`     | Pass the name of a file to `pip freeze` into. Only really useful with a virtual environment.
`run()`        | Either a single subtask or a list of subtasks to run. Each subtask may either be a Python function or a string that will be interpreted as a shell command.

### From Code

You can also use strap.py programmatically, if that's your cup of tea:

**COMING SOON**

## Why?

I found myself writing the same old code for every Python project to automate its installation. Conventional programmer's logic states that if you do it more than once, it should become a tool.