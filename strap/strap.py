from __future__ import print_function

import os
import sys
import platform
import re
import shutil
import contextlib
import imp


from collections import namedtuple

from clip import *
from utils import StrapException, directory, normalize_path, shell, ANSI


__version__ = '0.2.0'

STRAP_FILE = 'strapme.py'

# @TODO: Persistent cache in JSON file, cache subcommand
class DependencyCache:

	def __init__(self):
		self.cache = {}

	def load(self, module, check_func, install_func):
		log('Checking whether {} is installed...'.format(module), important=False)
		if module in self.cache or check_func():
			return
		log('{} not installed, installing now...'.format(module))
		try:
			install_func()
		except Exception as e:
			raise StrapException('Unable to install module {}: {}'.format(module, e.message))
		self.cache[module] = True


class Strap:

	def __init__(self):
		self._env = None
		self._silent = False
		self._depcache = DependencyCache()

	def _shell(self, command, force_global=False):
		'''Wrapper around shell() that can invoke relative to a virtual environment'''
		if self._env and not force_global:
			command = normalize_path('{}/{}'.format(self._env, command))
		try:
			ret = shell(command, self._silent)
			if ret != 0:
				raise StrapException('Return value {} on call to {}'.format(ret, command))
		except KeyboardInterrupt:
			pass

	def pip(self, command):
		def check_func():
			return shell('pip --version', silent=True) == 0
		def install_func():
			with directory(os.path.dirname(os.path.abspath(__file__))):  # This has to be done relative to strap.py
				self._shell('python lib/ez_setup.py')
				self._shell('python lib/get-pip.py')
		self._depcache.load('pip', check_func, install_func)

		self._shell('pip {}'.format(command))
		return self

	@contextlib.contextmanager
	def root(self, path):
		with directory(normalize_path(path)):
			yield

	@contextlib.contextmanager
	def virtualenv(self, path):
		try:
			def check_func():
				return shell('virtualenv --version', silent=True) == 0
			def install_func():
				self.pip('install virtualenv')
			self._depcache.load('virtualenv', check_func, install_func)

			path = normalize_path(path)

			# Check if our virtual environment is already created, and create if not
			log('Checking virtual environment')
			if not os.path.isdir(path):
				log('Creating virtual environment at {}...'.format(os.path.basename(path)))
				self._shell('virtualenv {}'.format(path), force_global=True)

			self._env = normalize_path('{}/{}'.format(path, 'Scripts' if platform.system() == 'Windows' else 'bin'))
			yield
		finally:
			self._env = None

	def freeze(self, filename):
		self.pip('freeze > {}'.format(filename))

	def run(self, task):
		if isinstance(task, (list, tuple)):
			for t in task:
				self.run(t)
		else:
			if hasattr(task, '__call__'):
				log('Running task {}'.format(ANSI.decorate(task.__doc__ or task.__name__, [ANSI.BOLD, ANSI.COLOR['cyan']])))
				task()
			else:
				# First check whether we can offload task to a function in this class
				fname, fargs = task.split(' ', 1)
				f = getattr(self, fname, None)
				if callable(f):
					f(fargs)
				self._shell(task)
		return self


strap = Strap()


def log(message, important=True):
	if important or not strap._silent:
		print('{} {}'.format(ANSI.decorate('[strap]', [ANSI.BOLD, ANSI.COLOR['green']]), message))


def _run(dir, tasks):
	with directory(dir):
		if not os.path.isfile(STRAP_FILE):
			raise Exception('Missing configuration file "{}"!'.format(STRAP_FILE))
		config = imp.load_source('strapme', os.path.abspath(STRAP_FILE))
		log('Running tasks on {}'.format(config.project if hasattr(config, 'project') else os.path.basename(dir)))
		setattr(config, 'strap', strap)
		for task in tasks:
			if not hasattr(config, task):
				log('"{}" not a valid task, skipping!'.format(task))
				continue
			strap.run(getattr(config, task))
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
	strap._shell('git clone {} {}'.format(url, dest), force_global=True)
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
		status = ANSI.decorate('There were errors.', ANSI.COLOR['red'])
	else:
		status = ANSI.decorate('No error!', ANSI.COLOR['green'])
	log('Strapping complete! {}'.format(status))

def funwrap(fun, args, silent, callback):
	try:
		strap._silent = silent
		fun(**args)
	except Exception as e:
		callback(e)
		return
	callback(None)


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
