![ok](https://raw.github.com/willyg302/strap.py/master/strap-logo.png "Everything is going to be ok")

-----

strap is Make for stupid people: a simple tool for cloning, copying, and initializing projects, because bootstrapping shouldn't be so gosh-durn hard. Inspired by [init-skeleton](https://github.com/paulmillr/init-skeleton).

You can read more about the motivations in [this blog post](http://willyg302.github.io/blog/#!/post/2014-09-15-strap-make-for-stupid-people).

## Install

strap assumes you have at least [Python 2.7](https://www.python.org/) and [git](http://git-scm.com/) installed. You can check whether you have these dependencies with the following commands:

```bash
$ python --version
$ git --version
```

If those return version strings and not errors, you're good to go!

1. Clone strap using git:

   ```bash
   $ git clone git@github.com:willyg302/strap.py.git
   ```

   ...or if you wish, download and unpack the ZIP from [GitHub](https://github.com/willyg302/strap.py).

2. Put the `strap.py/` directory somewhere convenient (for this readme, we will assume your home directory).

3. Run the following commands:

   ```bash
   $ cd strap.py
   $ python install.py
   ```

The following step is optional but highly recommended.

4. Add global aliases to your shell for using strap. How to do so depends on what shell you use, but for [bash](http://www.gnu.org/software/bash/) it is as simple as adding these lines to your `~/.bashrc`:

   ```
   alias sudo='sudo '
   alias strap='python ~/strap.py/strap'
   ```

   The first alias allows `sudo` to work with aliases. This is necessary because depending on what you do with strap, you may need elevated privileges to run a command. The second alias allows you to use strap by simply calling `strap`.

Congratulations, you're now ready to use strap!

## Usage

```bash
strap
strap [-h, --help] [--version] {init,run,cache} ...
```

Calling `strap` without any arguments is equivalent to `strap run default`.

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
            # Or if you prefer...
            strap.pip('install some-module').easy_install('this-other-module')
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

## Testing

Call `strap run test` while in the root directory of this repo. Yes, strap uses itself to test itself. No, you should not be surprised.

## Roadmap (v0.4.0)

- [x] Clean up and refactor existing code to be more modular
- [x] Add Node/NPM modules
- [ ] Basic tests
