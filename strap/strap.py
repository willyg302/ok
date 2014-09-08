from __future__ import print_function

import os
import sys
import platform
import re
import shutil
import contextlib
import json

from clip import *
from utils import *


__version__ = '0.3.0'


class DependencyCache:

	def __init__(self):
		self.save_on_close = True
		with strap_directory():
			if os.path.isfile('.depcache.json'):
				with open('.depcache.json', 'r') as f:
					self.cache = json.load(f)
			else:
				self.cache = {}

	def _save(self):
		with strap_directory():
			with open('.depcache.json', 'w') as f:
				json.dump(self.cache, f)

	def close(self):
		if self.save_on_close:
			self._save()

	def load(self, module, check_func, install_func):
		if self.cache.get(module):
			return
		log('Checking whether {} is installed...'.format(module), important=False)
		if check_func():
			self.cache[module] = True
			return
		log('{} not installed, installing now...'.format(module))
		try:
			install_func()
		except Exception as e:
			self.cache[module] = False
			raise StrapException('Unable to install module {}: {}'.format(module, e.message))
		self.cache[module] = True

	def clean(self):
		self.cache = {}
		log('Dependency cache successfully cleaned')

	def list(self):
		if not self.cache:
			log('Cache is empty')
			return
		for k in sorted(self.cache):
			print('{}{}'.format(ANSI.decorate('[failed] ', ANSI.COLOR['red']) if not self.cache[k] else '', k))


def module(check_func, install_func):
	def wrap(f):
		def wrapped_f(self, *args, **kwargs):
			self._depcache.load(f.__name__, lambda: check_func(self), lambda: install_func(self))
			return f(self, *args, **kwargs)
		return wrapped_f
	return wrap


class Strap:

	def __init__(self):
		self._env = None
		self._depcache = DependencyCache()
		self.silent = False
		self.notify_on_close = True

	def close(self, err):
		self._depcache.close()
		if self.notify_on_close:
			status, color = ('There were errors.', 'red') if err else ('No error!', 'green')
			log('Strapping complete! {}'.format(ANSI.decorate(status, ANSI.COLOR[color])))

	def _shell(self, command, force_global=False):
		'''Wrapper around shell() that can invoke relative to a virtual environment'''
		if self._env and not force_global:
			command = normalize_path('{}/{}'.format(self._env, command))
		try:
			ret = shell(command, self.silent)
			if ret != 0:
				raise StrapException('Return value {} on call to {}'.format(ret, command))
		except KeyboardInterrupt:
			pass

	def _install_easy_install(self):
		with strap_directory():  # This has to be done relative to strap.py
			self._shell('python lib/ez_setup.py')

	@module(lambda _: shell('easy_install --version', silent=True) == 0, _install_easy_install)
	def easy_install(self, command):
		self._shell('easy_install {}'.format(command))
		return self

	def _install_pip(self):
		with strap_directory():  # This has to be done relative to strap.py
			self.easy_install('--version')  # Ping to check if setuptools is installed
			self._shell('python lib/get-pip.py')

	@module(lambda _: shell('pip --version', silent=True) == 0, _install_pip)
	def pip(self, command):
		self._shell('pip {}'.format(command))
		return self

	def _install_virtualenv(self):
		self.pip('install virtualenv')

	@module(lambda _: shell('virtualenv --version', silent=True) == 0, _install_virtualenv)
	@contextlib.contextmanager
	def virtualenv(self, path):
		try:
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

	def _install_node(self):
		raise StrapException('Installation must be done manually.\nPlease visit http://nodejs.org/ for installation instructions.')

	@module(lambda _: shell('node --version', silent=True) == 0, _install_node)
	def node(self, command):
		self._shell('node {}'.format(command))
		return self

	@module(lambda _: shell('npm --version', silent=True) == 0, _install_node)
	def npm(self, command):
		self._shell('npm {}'.format(command))
		return self

	@contextlib.contextmanager
	def root(self, path):
		with directory(normalize_path(path)):
			yield

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
				fname, fargs = task.partition(' ')[::2]
				f = getattr(self, fname, None)
				if callable(f):
					f(fargs)
				self._shell(task)
		return self


strap = Strap()


def log(message, important=True):
	if important or not strap.silent:
		print('{} {}'.format(ANSI.decorate('[strap]', [ANSI.BOLD, ANSI.COLOR['green']]), message))

# Deletes [dir] if it exists and the user approves
def verify_write_directory(dir):
	if os.path.isdir(dir):
		if not App.confirm('The directory "{}" already exists! Overwrite?'.format(dir)):
			raise Exception('Operation aborted by user.')
		shutil.rmtree(dir)

# Clones a project from a remote URI [source] to [dest]
def clone(source, dest):
	verify_write_directory(dest)
	github = '(gh|github)\:(?://)?'
	url = 'git://github.com/{}.git'.format(re.sub(github, '', source)) if re.search(github, source) else source
	log('Cloning git repo "{}" to "{}"...'.format(url, dest))
	strap._shell('git clone {} {}'.format(url, dest), force_global=True)

# Copies a project from a local directory [source] to [dest]
def copy(source, dest):
	verify_write_directory(dest)
	log('Copying directory "{}" to "{}"...'.format(source, dest))
	shutil.copytree(source, dest)


app = App()
app.arg('--version', help='Print the version', action='version', version='strap version {}'.format(__version__))

@app.cmd(help='Clone a project and run its install task')
@app.cmd_arg('source', help='The directory or repo to clone from')
@app.cmd_arg('-d', '--dest', help='Where to initialize the project')
@app.cmd_arg('-s', '--silent', action='store_true')
def init(source, dest, silent=False):
	strap.silent = silent
	log('Fetching project')
	run_dir = dest
	if re.search('(?:https?|git(hub)?|gh)(?:://|@)?', source):
		clone(source, dest or os.getcwd())
	elif dest:
		copy(source, dest)
	else:
		run_dir = source
	run(['install'], run_dir)

@app.cmd(help='Run one or more tasks defined in a project\'s strapme file')
@app.cmd_arg('tasks', nargs='*', default=['default'], help='The task(s) to run')
@app.cmd_arg('-d', '--dir', default=os.getcwd(), help='Optional path to execute the tasks from')
@app.cmd_arg('-s', '--silent', action='store_true')
def run(tasks, dir, silent=False):
	strap.silent = silent
	with directory(dir):
		config = get_strapme(dir)
		log('Running tasks on {}'.format(config.project if hasattr(config, 'project') else os.path.basename(dir)))
		setattr(config, 'strap', strap)
		for task in tasks:
			if not hasattr(config, task):
				log('"{}" not a valid task, skipping!'.format(task))
				continue
			strap.run(getattr(config, task))
	log('All tasks complete!')

@app.cmd(help='Manage strap\'s dependency cache')
@app.cmd_arg('action', choices=['clean', 'list'])
def cache(action):
	strap.notify_on_close = False
	getattr(strap._depcache, action)()

@app.cmd(name='list', help='List the tasks defined in a project\'s strapme file')
def list_tasks():
	strap.notify_on_close = False
	from inspect import getmembers, isfunction
	d = {e[0]: e[1] for e in getmembers(get_strapme(), isfunction) if not e[0].startswith('_')}
	col_width = max(len(k) for k, v in d.iteritems()) + 2
	for k in sorted(d):
		print('{}{}'.format(k.ljust(col_width), d[k].__doc__ or ''))


def main():
	if len(sys.argv) == 1:
		sys.argv.append('run')  # Run default task
	err = None
	try:
		app.run()
	except ClipExit:
		# Parser-level exception, such as help/version or unrecognized argument
		strap.notify_on_close = False
	except Exception as e:
		err = e
		print(e, file=sys.stderr)
	finally:
		strap.close(err)

if __name__ == '__main__':
	main()
