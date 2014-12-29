An okfile is a file named `okfile.py`, usually placed at the root of your project (although it can exist elsewhere -- more on that later). The purpose of an okfile is twofold:

1. To define tasks that ok can run in your project
2. To automate installation of your project after an `ok init`

This is the bare minimum okfile possible:

```python
def install():
    pass

def default():
    pass
```

As you can see, you must at least define the "install" and "default" tasks. The "install" task is called during `ok init` immediately after your project has been cloned, while the "default" task is called when you simply type `ok` (which is an alias for `ok run default`).

However, this is a rather boring okfile. Let's look at a more typical example:

```python
import os

project = 'My Project Name'

def _print_cwd():
    print(os.getcwd())

def task_name():
    '''The optional name of this task'''
    ok.confirm('Are you ready to rumble?')
    with ok.root('subdirectory-of-project/to-run-task-in'):
        ok.run([
            'npm install',
            'bower install'
        ])
        # Or if you prefer...
        ok.run('npm install').run('bower install')
        # Or even better...
        ok.npm('install').bower('install')

def shell():
    '''Call shell functions? No problem.'''
    ok.run([
        'echo Hey there from the shell!',
        'pwd'
    ])

def python():
    '''Call Python functions? You got it.'''
    print('Hey there from Python!')
    _print_cwd()

def install():
    ok.run(task_name)

def default():
    ok.run([shell, python])
```

Assuming you placed this okfile in the `/home/somedude` directory, this has the following functionality:

```diff
$ ok list
default    
install    
python     Call Python functions? You got it.
shell      Call shell functions? No problem.
task_name  The optional name of this task
$ ok
[ok] Running tasks on My Project Name
[ok] Running task default
[ok] Running task Call shell functions? No problem.
Hey there from the shell!
/home/somedude
[ok] Running task Call Python functions? You got it.
Hey there from Python!
/home/somedude
[ok] All tasks complete!
[ok] Complete! No error!
$ ok run shell python
[ok] Running tasks on My Project Name
[ok] Running task Call shell functions? No problem.
Hey there from the shell!
/home/somedude
[ok] Running task Call Python functions? You got it.
Hey there from Python!
/home/somedude
[ok] All tasks complete!
[ok] Complete! No error!
$ ok run install
[ok] Running tasks on My Project Name
[ok] Running task install
[ok] Running task The optional name of this task
Are you ready to rumble? [y/n]: n
Operation aborted by user
```

We're not going to run the install task because that would most definitely throw an error, but rest assured that it *would* invoke NPM and Bower if everything were set up correctly.

Note that, as above, you can do anything in the okfile that you would normally do in a Python script, including importing needed modules. However, it is best to stick with standard or globally-installed modules, such as `os` or `sys`.

## The `ok` Variable









<!-- @TODO: Below from old readme -->


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
