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

from subprocess import call
from lib.docopt import docopt


STRAP_FILE = 'strapme.py'
ENV = None

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
	try:
		if force_global or not ENV:
			call(command, shell=True)
		else:
			call('{}{}{}'.format(ENV, script_dir, command), shell=True)
	except KeyboardInterrupt:
		pass

def log(level, message):
	print('[strap] {}> {}'.format('=' * level, message))

def normalize_path(path):
	return path.replace('/', os.sep)


# Checks to see if [package] is installed, and if not calls [command] to install it
def bootstrap_package(package, command):
	print('Checking whether {} is installed...'.format(package))
	try:
		importlib.import_module(package)
	except ImportError:
		print('{} not installed, installing now...'.format(package))
		shell(command, force_global=True)

# Check for and installs dependencies
def check_dependencies():
	log(3, 'Checking dependencies')
	with directory(os.path.dirname(os.path.abspath(__file__))):  # This has to be done relative to strap.py
		bootstrap_package('setuptools', 'python lib/ez_setup.py')
		bootstrap_package('pip', 'python lib/get-pip.py')
		bootstrap_package('virtualenv', 'pip install virtualenv')

# Check if our virtual environment is already created, and create if not
def check_env():
	if not ENV:
		return
	log(2, 'Checking virtual environment')
	if not os.path.isdir(ENV):
		print('Creating virtual environment at {}...'.format(os.path.basename(ENV)))
		shell('virtualenv {}'.format(ENV), force_global=True)

def run_task(tasklist, taskname):
	task = tasklist[taskname]
	log(3, 'Running task {}'.format(task['name'] if 'name' in task else taskname))
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
		log(5, 'Running tasks on {}'.format(config['project'] if 'project' in config else os.path.basename(dir)))
		check_dependencies()
		for task in tasks:
			if task in config['tasks']:
				run_task(config['tasks'], task)
			else:
				print('"{}" not a valid task, skipping!'.format(task))
	log(5, 'All tasks complete!')


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
	print('Cloning git repo "{}" to "{}"...'.format(url, dest))
	shell('git clone {} {}'.format(url, dest), force_global=True)
	_run(dest, ['install'])

# Copies a project from a local directory [source] to [dest]
def copy(source, dest):
	verify_write_directory(dest)
	print('Copying directory "{}" to "{}"...'.format(source, dest))
	shutil.copytree(source, dest)
	_run(dest, ['install'])

def _init(source, dest):
	log(5, 'Fetching project')
	if re.search('(?:https?|git(hub)?|gh)(?:://|@)?', source):
		clone(source, dest if dest else os.getcwd())
	elif dest:
		copy(source, dest)
	else:
		_run(source, ['install'])


def done(err):
	if err:
		print(err, file=sys.stderr)
	log(5, 'Strapping complete! {}'.format('There were errors.' if err else 'No error!'))

def run(dir, tasks, callback=done):
	'''usage: strap run -h
       strap run [-v] [--dir=PATH] <task>...

options:
  -h, --help
  -v, --verbose
  -d PATH --dir PATH
  '''
	try:
		_run(dir, tasks)
	except Exception, e:
		callback(e)
		return
	callback(None)

def init(source, dest, callback=done):
	'''usage: strap init -h
       strap init [-v] [--dest=PATH] <source>

options:
  -h, --help
  -v, --verbose
  -d PATH --dest PATH
  '''
	try:
		_init(source, dest)
	except Exception, e:
		callback(e)
		return
	callback(None)


def main():
	args = docopt(__doc__, version='strap version 0.1.0', options_first=True)
	command = args['<command>']
	argv = [command] + args['<args>']
	if not command:
		command = 'run'
		argv = ['run', 'default']

	if command == 'help':
		if args['<args>'] and args['<args>'][0] in 'init run'.split():
			print(docopt(globals()[args['<args>'][0]].__doc__, argv=['-h']))
		else:
			print(__doc__.strip('\n'))
	elif command == 'init':
		subargs = docopt(init.__doc__, argv=argv)
		init(subargs['<source>'], subargs['--dest'])
	elif command == 'run':
		subargs = docopt(run.__doc__, argv=argv)
		run(subargs['--dir'] or os.getcwd(), subargs['<task>'])
	else:
		print('Invalid command "{}". See "strap help".'.format(command))


if __name__ == '__main__':
	main()