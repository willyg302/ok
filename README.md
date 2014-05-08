# strap.py

---

A simple tool for cloning, copying, and initializing Python projects, because bootstrapping shouldn't be so gosh-durn hard. Inspired by [init-skeleton](https://github.com/paulmillr/init-skeleton).

## Install

Clone this repo and put the `strap/` directory somewhere convenient (for this readme, we will assume the user's home directory). It's also immensely helpful to alias `python ~/strap` to something like `strap`.

## Usage

### init

`strap init <source> [--dest destination]`

`source` can either be a directory or a GitHub repo URI. `destination` is an optional directory. If `destination` is given, then `source` will be cloned or copied into it. If `destination` is omitted, then `source` will either be cloned into the current working directory (if it is a URI) or "refreshed" (if it is a directory, the equivalent of `strap run install`).

**Examples**:

```bash
strap init ../somedir/otherdir/strap-this
strap init copy/this --dest ../to/here/and-then-strap-it
strap init https://github.com/willyg302/Parrot
strap init gh:willyg302/jarvis
strap init git@github.com:willyg302/jarvis.git --dest ~/jarvis-test
```

### run

`strap run <task>... [--dir directory]`

You can provide a list of one or more `task` to run. If given, `directory` specifies the path to execute tasks from; it defaults to the current working directory. Note that calling `strap` (no arguments) is equivalent to `strap run default`.

**Examples**:

```bash
strap
strap run sometask
strap run task_a task_b also_do_this --dir from/this/directory
```

### strapme.py

Once a project is fetched with `strap init`, it will be installed according to the rules defined in `strapme.py` located at its root directory.

```python
import os

def print_cwd():
    print('Hello from {}!'.format(os.getcwd()))

config = {
    'project': 'My Optional Project Name',
    'tasks': {
        'task_name': {
            'name': 'The optional name of this task',
            'root': 'subdirectory-of-project/to-run-task-in',
            'virtualenv': 'virtual-environment-name',
            'run': [
                'pip install some-module',
                'easy_install this-other-module'
            ],
            'freeze': 'requirements.txt'
        },
        'shell': {
            'run': [
                'echo Oh yeah I can run other stuff too!',
                'npm install'
            ]
        },
        'python': {
            'name': 'Call a Python function? No problem.',
            'root': '../lets-do-it-here',
            'run': [print_cwd]
        },
        'install': {
            'run': ['task_name', 'shell', 'python']
        },
        'default': {
            'run': ['install']
        }
    }
}
```

`strapme.py` must contain a Python dictionary called `config`. This dict defines project metadata and holds a dictionary of `tasks` that may be run. The "install" and "default" tasks are required; without them, you'll probably get errors.

Tasks are run sequentially and fully separate from each other. With the exception of the `run` array, all task properties are optional. If a `virtualenv` is given, then subtasks defined in `run` will be executed relative to the virtual environment. You may also specify a `root` directory to execute all tasks in (this includes building the virtual environment).

`run` may contain the name of another task defined in `tasks`, a shell command, or the name of a Python function defined globally in `strapme.py`. Note that while this system allows imports, it is best to stick with standard or globally-installed modules.

### From Code

You can also use strap.py programmatically, if that's your cup of tea:

**COMING SOON**

## Why?

I found myself writing the same old code for every Python project to automate its installation. Conventional programmer's logic states that if you do it more than once, it should become a tool.