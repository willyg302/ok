from __future__ import print_function

import os
import sys
import platform
import importlib
import re
import shutil
import json
import contextlib

from subprocess import call


STRAP_FILE = 'strap.json'
ENV = None

script_dir = '\\Scripts\\' if platform.system() == 'Windows' else '/bin/'


@contextlib.contextmanager
def directory(path):
	'''Context manager for changing the current working directory'''
	prev_cwd = os.getcwd()
	os.chdir(path)
	try:
		yield
	finally:
		os.chdir(prev_cwd)


# Checks to see if [package] is installed, and if not calls [command] to install it
def bootstrap_package(package, command):
	print('Checking whether {} is installed...'.format(package))
	try:
		importlib.import_module(package)
	except ImportError:
		print('{} not installed, installing now...'.format(package))
		call(command, shell=True)

# Invokes a shell command relative to our virtual environment
def call_virtual(command):
	call('{}{}{}'.format(ENV, script_dir, command), shell=True)


# Check for and installs dependencies
def check_dependencies():
	print('== 1. Checking dependencies ==')
	bootstrap_package('setuptools', 'python setup/ez_setup.py')
	bootstrap_package('pip', 'python setup/get-pip.py')
	bootstrap_package('virtualenv', 'pip install virtualenv')

# Check if our virtual environment is already created, and create if not
def check_env():
	if not ENV:
		return
	print('== 2. Checking virtual environment ==')
	if not os.path.isdir(ENV):
		print('Creating virtual environment at {}...'.format(os.path.basename(ENV)))
		call('virtualenv {}'.format(ENV), shell=True)

# Install all necessary requirements to the virtual environment
def install_requirements(requirements):
	print('== 3. Installing requirements ==')
	for requirement in requirements:
		call_virtual(requirement)


def install(root):
	if not os.path.isdir(root):
		raise Exception('"{}" is not a valid directory!'.format(root))
	with directory(root):
		if not os.path.isfile(STRAP_FILE):
			raise Exception('Missing configuration file "{}"!'.format(STRAP_FILE))
		with open(STRAP_FILE) as f:
			config = json.load(f)
		print('=== Installing {} ==='.format(config['project']))
		check_dependencies()
		for task in config['tasks']:
			task_root = task['root'] if 'root' in task else '.'
			global ENV
			ENV = task['virtualenv'] if 'virtualenv' in task else None
			if not os.path.isdir(task_root):
				raise Exception('"{}" is not a valid directory!'.format(task_root))
			with directory(task_root):
				check_env()
				install_requirements(task['requirements'])
				if 'freeze' in task:
					call_virtual('pip freeze > {}'.format(task['freeze']))
	print('=== {} Installation Complete! ==='.format(config['project']))


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

# Clones a project from a remote URI [source] into [dest]
def clone(source, dest):
	verify_write_directory(dest)
	github = '(gh|github)\:(?://)?'
	url = 'git://github.com/{}.git'.format(re.sub(github, '', source)) if re.search(github, source) else source
	print('Cloning git repo "{}" to "{}"...'.format(url, dest))
	call('git clone {} {}'.format(url, dest), shell=True)
	install(dest)

# Copies a project from a local directory [source] to [dest]
def copy(source, dest):
	verify_write_directory(dest)
	shutil.copytree(source, dest)
	install(dest)

def done(err):
	if err:
		print(err, file=sys.stderr)
	print('=== Strapping complete! {} ==='.format('There were errors.' if err else 'No error!'))

def run(source, dest=None, callback=None):
	print('=== Fetching project ===')
	if not callback:
		callback = done
	try:
		if re.search('(?:https?|git(hub)?|gh)(?:://|@)?', source):
			clone(source, dest if dest else os.getcwd())
		else:
			if dest:
				copy(source, dest)
			else:
				install(source)
	except Exception, e:
		callback(e)
		return
	callback(None)


def main():
	if len(sys.argv) < 2:
		print('Usage: strap <uri-or-path-to-repo> [path-to-output-dir]')
		return
	source = sys.argv[1]
	dest = sys.argv[2] if len(sys.argv) > 2 else ''
	run(source, dest)


if __name__ == '__main__':
	main()