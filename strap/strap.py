import os
import platform
import importlib

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


def main():
	print('== Installing jarvis Kernel ==')
	os.chdir(DIRNAME)  # Make sure we work in directory next to current file
	check_dependencies()
	check_env()
	install_requirements()
	print('== Kernel Installation Complete! ==')


if __name__ == '__main__':
	main()