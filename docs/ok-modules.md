ok has a module system for interfacing with other build tools and programs, e.g. Gulp and Make. Modules are currently hosted at the [ok-modules](https://github.com/willyg302/ok-modules) repository.

In this section you will learn more about the module system and module management, as well as how to write your very own module.

## Why Modules?

Behind the scenes, most modules defer directly to shell commands. For example, the following are equivalent:

```python
ok.npm('install')
ok.run('npm install')
```

This begs the question: why have modules at all?

### Painless Bootstrapping

Suppose the user does not have Node/NPM installed when `ok.run('npm install')` is called. What would happen? Most likely the shell would throw an error about a command not being found, and the user would have to investigate the source of the issue, reason that they need this thing called "npm" and then go about trying to install it. If your install script is smart, it might try to catch the error and print a more useful message to the user. But why include all this logic when ok can do it for you?

That's what happens when `ok.npm('install')` is called. The npm module first checks whether NPM is installed, then runs the command if it is. Otherwise, a "smart" error is thrown. All this logic is integrated into the module system, so it happens automatically whenever your okfile uses a module. In this way, your users can go from zero (a vanilla machine) to hero (hacking on your project) without you having to:

- write complicated install scripts
- write long and off-putting installation instructions

### Sensible Defaults

In some cases, modules can improve upon standard command line usage. For example, the following are equivalent:

```python
ok.run('node_modules/.bin/gulp')
ok.node('gulp', module=True)
```

This tells node to run the locally-installed executable module `gulp`, which lives in the `node_modules/.bin/` directory. However, it's quite inconvenient to have to hard-code, let alone remember, Node's local module path. It is for this reason that ok's node module provides the `module=True` keyword argument.

You can include these kinds of "sensible defaults" in your modules. Remember: anything that's possible in Python, and that makes a developer's life easier, is fair game.

## The Module System

The entire module system lives in the `ok/modules/` directory of your ok installation. This directory contains any downloaded modules, as well as the `.cache.json` and `.registry.json` files.

### Module States

At any given time, modules may be in one of three states:

- **Not Downloaded**: Modules must be grabbed from the ok-modules repository. A module that has not been downloaded has *never* been used, since as soon as a module is called upon from an okfile it is automatically downloaded.
- **Not Verified**: Once a module is downloaded, it is *verified*. Verification entails checking whether the system supports that module:

  ```python
  return ok.ping('virtualenv --version')  # If True, we're good!
  ```

  and installing it if not:

  ```python
  ok.pip('install virtualenv')
  ```
- **Verified**: Only when a module reaches this state can it be used.

### The Cache

`.cache.json` is a dictionary keyed by module name, whose values are True if the module is verified and False otherwise. If a module is not in the cache, it is assumed to be not downloaded.

The cache is law, meaning that deleting this file is the same as deleting the entire `modules/` directory. You can also achieve this effect by calling `ok modules clean`.

### The Registry

ok maintains a registry of available modules. The global registry can be viewed [here](https://raw.githubusercontent.com/willyg302/ok-modules/master/registry.json).

Your local `.registry.json` is a mirror of this global registry. ok uses `.registry.json` to check whether a given module exists, and errors if a module is not listed. It is therefore important to keep your local mirror up to date with the global registry by calling `ok modules sync`.

## Module Management

Use `ok modules list` to list your currently downloaded modules, or `ok modules list -a` to list all available modules.

<!-- @TODO -->

## Writing Your Own Module

Now that you know more about modules, it's time to write your own! In this example we'll walk through writing and using a Python module.

> **NOTE**: This example is pointless because ok cannot even run without Python installed, which is why there is no Python module for ok. It is hoped that your custom modules are more useful.

### The Code

First, let's consider how we would know whether Python is installed on a system. This one's simple: we just call `python --version` from the command line, and if it throws an error then Python doesn't exist.

The harder task is how to actually install Python for the user. When writing modules, you have several options for this part:

- Defer to another module. For example, the virtualenv module simply calls `ok.pip('install virtualenv')`.
- Attempt an automated install. An example is pip, which fetches an install script from the pip website and runs it from a temporary directory. Note that such an install usually gets complicated, especially when the process isn't consistent across platforms.
- Print a nice error message.

In this case we'll choose the last option, and redirect users to the [Python website](https://www.python.org/).

Finally, we must handle the `run()` method. As this is a simple wrapper around the Python CLI, we shell out to it with our required command (since the REPL isn't supported) and return `ok` for chaining.

Here's our finished module:

```python
def check():
	return ok.ping('python --version')

def install():
	raise utils.OkException('''Installation must be done manually.
Please visit https://www.python.org/ for installation instructions.''')

def run(command):
	ok.shell('python {}'.format(command))
	return ok
```

### Submitting the Module

The next step is to submit the module for inclusion in the ok-modules repository.

1. [Fork](https://help.github.com/articles/fork-a-repo/) the [ok-modules](https://github.com/willyg302/ok-modules) repository
2. Add the above code to a file named `python.py` in the `modules/` directory of the repository
3. Call `ok` -- this will rebuild the registry
4. Submit a [pull request](https://help.github.com/articles/using-pull-requests/)

Once the pull request has been accepted, your module is live and ready for use in ok!

### Using the Module

1. Call `ok modules sync` to sync with the updated registry
2. Call `ok modules list -a | grep python` to check whether the Python module has been included in the list of available modules
3. Use `ok.python('some command here')` in an okfile like normal
4. Profit

Note that it may take several seconds for the registry to update after the pull request has been merged, so if your module is not listed initially wait a while and try again.
