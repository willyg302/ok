import os
import sys
import platform
import importlib
import re

from subprocess import call


DIRNAME = os.path.abspath(os.path.dirname(__file__))
ENV = 'env'
REQUIREMENTS = 'requirements.txt'

script_dir = '\\Scripts\\' if platform.system() == 'Windows' else '/bin/'


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
	print('== 2. Checking virtual environment ==')
	if not os.path.isdir(ENV):
		print('Creating virtual environment at {}...'.format(os.path.basename(ENV)))
		call('virtualenv {}'.format(ENV), shell=True)

# Install all necessary requirements to the virtual environment
def install_requirements():
	print('== 3. Installing requirements ==')
	call_virtual('pip install sockjs-tornado')
	call_virtual('pip freeze > {}'.format(REQUIREMENTS))


def install(root):
	print('== Installing jarvis Kernel ==')
	# @TODO: Error-check that this exists
	os.chdir(root)  # Make sure we work in appropriate directory

	print os.getcwd()
	# check_dependencies()
	# check_env()
	# install_requirements()
	print('== Kernel Installation Complete! ==')




# Clones a project from a remote URI [source] into [dest]
def clone(source, dest):
	github = '(gh|github)\:(?://)?'
	url = 'git://github.com/{}.git'.format(re.sub(github, '', source)) if re.search(github, source) else source
	print('Cloning git repo "{}" to "{}"...'.format(url, dest))
	call('git clone {} {}'.format(url, dest), shell=True)
	install(dest)

def copy(source, dest):
	print 'copy'


def done(err):
	print('=== Strapping complete! {} ==='.format(err if err else 'No error!'))


def run(source, dest=None, callback=None):
	print('=== Fetching project ===')
	if not callback:
		callback = done
	if re.search('(?:https?|git(hub)?|gh)(?:://|@)?', source):
		clone(source, dest if dest else os.getcwd())
	else:
		if dest:
			copy(source, dest)
		else:
			install(source)
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