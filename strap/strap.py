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

import click


__version__ = '0.2.0'

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
	log(4, 'Checking whether {} is installed...'.format(package), important=False)
	try:
		importlib.import_module(package)
	except ImportError:
		log(4, '{} not installed, installing now...'.format(package))
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
			log(2, 'Running task {}'.format(task.__doc__ or task.__name__))
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
		log(0, 'Running tasks on {}'.format(config.project if hasattr(config, 'project') else os.path.basename(dir)))
		check_dependencies()
		setattr(config, 'strap', api)
		for task in tasks:
			if not hasattr(config, task):
				log(2, '"{}" not a valid task, skipping!'.format(task))
				continue
			run_task(getattr(config, task))
	log(0, 'All tasks complete!')


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
		clone(source, dest or os.getcwd())
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


def print_version(ctx, value):
	if not value:
		return
	click.echo('strap version {}'.format(__version__))
	ctx.exit()

@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--version', is_flag=True, callback=print_version, expose_value=False, is_eager=True)
def main(ctx):
	if not ctx.invoked_subcommand:
		ctx.invoke(run, tasks=(u'default',), dir=os.getcwd(), verbose=False)

@main.command()
@click.argument('source')
@click.option('--dest', '-d')
@click.option('--verbose', '-v', is_flag=True)
def init(source, dest, verbose, callback=done):
	funwrap(_init, {'source': source, 'dest': dest}, verbose, callback)

@main.command()
@click.argument('tasks', nargs=-1)
@click.option('--dir', '-d', default=os.getcwd())
@click.option('--verbose', '-v', is_flag=True)
def run(tasks, dir, verbose, callback=done):
	funwrap(_run, {'dir': dir, 'tasks': list(tasks)}, verbose, callback)


if __name__ == '__main__':
	main()