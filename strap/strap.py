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
from collections import namedtuple

from clip import *
from utils import directory, normalize_path, ANSI


__version__ = '0.2.0'

STRAP_FILE = 'strapme.py'
ENV = None
SILENT = False

script_dir = '\\Scripts\\' if platform.system() == 'Windows' else '/bin/'


# Wrapper around call() that handles invoking relative to a virtual environment
def shell(command, force_global=False):
	if ENV and not force_global:
		command = '{}{}{}'.format(ENV, script_dir, command)
	try:
		if not SILENT:
			call(command, shell=True)
		else:
			with open(os.devnull, 'w') as fnull:
				call(command, stdout=fnull, stderr=STDOUT, shell=True)
	except KeyboardInterrupt:
		pass


def log(message, important=True):
	if important or not SILENT:
		print('{} {}'.format(ANSI.decorate('[strap]', [ANSI.BOLD, ANSI.COLOR['green']]), message))


# Checks to see if [package] is installed, and if not calls [command] to install it
def bootstrap_package(package, command):
	log('Checking whether {} is installed...'.format(package), important=False)
	try:
		importlib.import_module(package)
	except ImportError:
		log('{} not installed, installing now...'.format(package))
		shell(command, force_global=True)

# Check for and installs dependencies
def check_dependencies():
	log('Checking dependencies')
	with directory(os.path.dirname(os.path.abspath(__file__))):  # This has to be done relative to strap.py
		bootstrap_package('setuptools', 'python lib/ez_setup.py')
		bootstrap_package('pip', 'python lib/get-pip.py')
		bootstrap_package('virtualenv', 'pip install virtualenv')

# Check if our virtual environment is already created, and create if not
def check_env():
	if not ENV:
		return
	log('Checking virtual environment')
	if not os.path.isdir(ENV):
		log('Creating virtual environment at {}...'.format(os.path.basename(ENV)))
		shell('virtualenv {}'.format(ENV), force_global=True)


@contextlib.contextmanager
def root(path):
	with directory(normalize_path(path)):
		yield

@contextlib.contextmanager
def virtualenv(path):
	global ENV
	try:
		ENV = normalize_path(path)
		check_env()
		yield
	finally:
		ENV = None

def freeze(filename):
	shell('pip freeze > {}'.format(filename))

def run_task(task):
	if isinstance(task, (list, tuple)):
		for t in task:
			run_task(t)
	else:
		if hasattr(task, '__call__'):
			log('Running task {}'.format(task.__doc__ or task.__name__))
			task()
		else:
			shell(task)

api = namedtuple('API', 'root virtualenv shell freeze run')(
	root=root,
	virtualenv=virtualenv,
	shell=shell,
	freeze=freeze,
	run=run_task
)


def _run(dir, tasks):
	with directory(dir):
		if not os.path.isfile(STRAP_FILE):
			raise Exception('Missing configuration file "{}"!'.format(STRAP_FILE))
		config = imp.load_source('strapme', os.path.abspath(STRAP_FILE))
		log('Running tasks on {}'.format(config.project if hasattr(config, 'project') else os.path.basename(dir)))
		check_dependencies()
		setattr(config, 'strap', api)
		for task in tasks:
			if not hasattr(config, task):
				log('"{}" not a valid task, skipping!'.format(task))
				continue
			run_task(getattr(config, task))
	log('All tasks complete!')


# Deletes [dir] if it exists and the user approves
def verify_write_directory(dir):
	if os.path.isdir(dir):
		if not click.confirm('The directory "{}" already exists! Overwrite?'.format(dir)):
			raise Exception('Operation aborted by user.')
		shutil.rmtree(dir)

# Clones a project from a remote URI [source] to [dest]
def clone(source, dest):
	verify_write_directory(dest)
	github = '(gh|github)\:(?://)?'
	url = 'git://github.com/{}.git'.format(re.sub(github, '', source)) if re.search(github, source) else source
	log('Cloning git repo "{}" to "{}"...'.format(url, dest))
	shell('git clone {} {}'.format(url, dest), force_global=True)
	_run(dest, ['install'])

# Copies a project from a local directory [source] to [dest]
def copy(source, dest):
	verify_write_directory(dest)
	log('Copying directory "{}" to "{}"...'.format(source, dest))
	shutil.copytree(source, dest)
	_run(dest, ['install'])

def _init(source, dest):
	log('Fetching project')
	if re.search('(?:https?|git(hub)?|gh)(?:://|@)?', source):
		clone(source, dest or os.getcwd())
	elif dest:
		copy(source, dest)
	else:
		_run(source, ['install'])


def done(err):
	if err:
		print(err, file=sys.stderr)
	log('Strapping complete! {}'.format('There were errors.' if err else 'No error!'))

def funwrap(fun, args, silent, callback):
	try:
		global SILENT
		SILENT = silent
		fun(**args)
	except Exception, e:
		callback(e)
		return
	callback(None)


# @TODO: Add help strings
app = App()
app.arg('--version', help='Print the version', action='version', version='strap version {}'.format(__version__))

@app.cmd(help='Clone a project and run its install task')
@app.cmd_arg('source', help='The directory or repo to clone from')
@app.cmd_arg('-d', '--dest', help='Where to initialize the project')
@app.cmd_arg('-s', '--silent', action='store_true')
def init(source, dest, silent, callback=done):
	funwrap(_init, {'source': source, 'dest': dest}, silent, callback)

@app.cmd(help='Run one or more tasks defined in a project\'s strapme file')
@app.cmd_arg('tasks', nargs='*', default=['default'], help='The task(s) to run')
@app.cmd_arg('-d', '--dir', default=os.getcwd(), help='Optional path to execute the tasks from')
@app.cmd_arg('-s', '--silent', action='store_true')
def run(tasks, dir, silent, callback=done):
	funwrap(_run, {'dir': dir, 'tasks': list(tasks)}, silent, callback)


def main():
	if len(sys.argv) == 1:
		sys.argv.append('run')  # Run default task
	try:
		app.run()
	except ClipExit as e:
		pass

if __name__ == '__main__':
	main()
