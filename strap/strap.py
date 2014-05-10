'''
usage: strap
       strap (--version)
       strap <command> [<args>...]

options:
  -h, --help

Subcommands include:
  init  Initialize a project
  run   Run tasks on a project

See 'strap help <command>' for more information on a specific command.
  '''
from __future__ import print_function

import os
import sys
import platform
import importlib
import re
import shutil
import contextlib
import imp

from subprocess import call, STDOUT
from lib.docopt import docopt


__version__ = '0.1.0'

STRAP_FILE = 'strapme.py'
ENV = None
VERBOSE = False

script_dir = '\\Scripts\\' if platform.system() == 'Windows' else '/bin/'


@contextlib.contextmanager
def directory(path):
	'''Context manager for changing the current working directory'''
	if not os.path.isdir(path):
		raise Exception('"{}" is not a valid directory!'.format(path))
	prev_cwd = os.getcwd()
	os.chdir(path)
	try:
		yield
	finally:
		os.chdir(prev_cwd)


# Wrapper around call() that handles invoking relative to a virtual environment
def shell(command, force_global=False):
	if ENV and not force_global:
		command = '{}{}{}'.format(ENV, script_dir, command)
	try:
		if VERBOSE:
			call(command, shell=True)
		else:
			with open(os.devnull, 'w') as fnull:
				call(command, stdout=fnull, stderr=STDOUT, shell=True)
	except KeyboardInterrupt:
		pass

def log(level, message, important=True):
	if VERBOSE or important:
		print('{}[strap] => {}'.format(' ' * level, message))

def normalize_path(path):
	return path.replace('/', os.sep)


# Checks to see if [package] is installed, and if not calls [command] to install it
def bootstrap_package(package, command):
	log(2, 'Checking whether {} is installed...'.format(package), important=False)
	try:
		importlib.import_module(package)
	except ImportError:
		log(2, '{} not installed, installing now...'.format(package))
		shell(command, force_global=True)

# Check for and installs dependencies
def check_dependencies():
	log(2, 'Checking dependencies')
	with directory(os.path.dirname(os.path.abspath(__file__))):  # This has to be done relative to strap.py
		bootstrap_package('setuptools', 'python lib/ez_setup.py')
		bootstrap_package('pip', 'python lib/get-pip.py')
		bootstrap_package('virtualenv', 'pip install virtualenv')

# Check if our virtual environment is already created, and create if not
def check_env():
	if not ENV:
		return
	log(4, 'Checking virtual environment')
	if not os.path.isdir(ENV):
		log(4, 'Creating virtual environment at {}...'.format(os.path.basename(ENV)))
		shell('virtualenv {}'.format(ENV), force_global=True)

def run_task(tasklist, taskname):
	task = tasklist[taskname]
	log(2, 'Running task {}'.format(task['name'] if 'name' in task else taskname))
	task_root = normalize_path(task['root']) if 'root' in task else '.'
	global ENV
	ENV = normalize_path(task['virtualenv']) if 'virtualenv' in task else None
	with directory(task_root):
		check_env()
		for item in task['run']:
			if hasattr(item, '__call__'):
				item()
			elif isinstance(item, basestring):
				if item in tasklist:
					run_task(tasklist, item)
				else:
					shell(item)
		if 'freeze' in task:
			shell('pip freeze > {}'.format(task['freeze']))

def _run(dir, tasks):
	with directory(dir):
		if not os.path.isfile(STRAP_FILE):
			raise Exception('Missing configuration file "{}"!'.format(STRAP_FILE))
		config = imp.load_source('strapme', os.path.abspath(STRAP_FILE)).config
		log(0, 'Running tasks on {}'.format(config['project'] if 'project' in config else os.path.basename(dir)))
		check_dependencies()
		for task in tasks:
			if task in config['tasks']:
				run_task(config['tasks'], task)
			else:
				log(2, '"{}" not a valid task, skipping!'.format(task))
	log(0, 'All tasks complete!')


def query_yes_no(query, default='yes'):
	valid = {
		'yes': True,
		'y': True,
		'no': False,
		'n': False
	}
	if default not in ['yes', 'no', None]:
		default = None
	while True:
		choice = raw_input('{} [{}/{}]: '.format(query, 'Y' if default == 'yes' else 'y', 'N' if default == 'no' else 'n')).lower()
		if default and not choice:
			return valid[default]
		elif choice in valid:
			return valid[choice]
		else:
			print('Please respond with "yes" or "no" (or "y" or "n").')

# Deletes [dir] if it exists and the user approves
def verify_write_directory(dir):
	if os.path.isdir(dir):
		if not query_yes_no('The directory "{}" already exists! Overwrite?'.format(dir)):
			raise Exception('Operation aborted by user.')
		shutil.rmtree(dir)

# Clones a project from a remote URI [source] to [dest]
def clone(source, dest):
	verify_write_directory(dest)
	github = '(gh|github)\:(?://)?'
	url = 'git://github.com/{}.git'.format(re.sub(github, '', source)) if re.search(github, source) else source
	log(2, 'Cloning git repo "{}" to "{}"...'.format(url, dest))
	shell('git clone {} {}'.format(url, dest), force_global=True)
	_run(dest, ['install'])

# Copies a project from a local directory [source] to [dest]
def copy(source, dest):
	verify_write_directory(dest)
	log(2, 'Copying directory "{}" to "{}"...'.format(source, dest))
	shutil.copytree(source, dest)
	_run(dest, ['install'])

def _init(source, dest):
	log(0, 'Fetching project')
	if re.search('(?:https?|git(hub)?|gh)(?:://|@)?', source):
		clone(source, dest if dest else os.getcwd())
	elif dest:
		copy(source, dest)
	else:
		_run(source, ['install'])


def done(err):
	if err:
		print(err, file=sys.stderr)
	log(0, 'Strapping complete! {}'.format('There were errors.' if err else 'No error!'))

def funwrap(fun, args, verbose, callback):
	try:
		global VERBOSE
		VERBOSE = verbose
		fun(**args)
	except Exception, e:
		callback(e)
		return
	callback(None)

def run(dir, tasks, verbose=False, callback=done):
	'''usage: strap run -h
       strap run [-v] [--dir=PATH] <task>...

options:
  -h, --help
  -v, --verbose
  -d PATH --dir PATH
  '''
	funwrap(_run, {'dir': dir, 'tasks': tasks}, verbose, callback)

def init(source, dest, verbose=False, callback=done):
	'''usage: strap init -h
       strap init [-v] [--dest=PATH] <source>

options:
  -h, --help
  -v, --verbose
  -d PATH --dest PATH
  '''
	funwrap(_init, {'source': source, 'dest': dest}, verbose, callback)


def main():
	parsed = docopt(__doc__, version='strap version {}'.format(__version__), options_first=True)
	command = parsed['<command>']
	args = parsed['<args>']
	argv = [command] + args
	if not command:
		command = 'run'
		argv = ['run', 'default']

	if command == 'help':
		if args and args[0] in 'init run'.split():
			print(docopt(globals()[args[0]].__doc__, argv=['-h']))
		else:
			print(__doc__.strip('\n'))
	elif command == 'init':
		subargs = docopt(init.__doc__, argv=argv)
		init(subargs['<source>'], subargs['--dest'], verbose=subargs['--verbose'])
	elif command == 'run':
		subargs = docopt(run.__doc__, argv=argv)
		run(subargs['--dir'] or os.getcwd(), subargs['<task>'], verbose=subargs['--verbose'])
	else:
		print('Invalid command "{}". See "strap help".'.format(command))


if __name__ == '__main__':
	main()