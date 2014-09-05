from __future__ import print_function

import os
import sys
import platform
import re
import shutil
import contextlib
import imp
import json


from collections import namedtuple

from clip import *
from utils import StrapException, directory, normalize_path, shell, ANSI


__version__ = '0.3.0'

STRAP_FILE = 'strapme.py'


class DependencyCache:

	def __init__(self):
		with directory(os.path.dirname(os.path.abspath(__file__))):
			if os.path.isfile('.depcache.json'):
				with open('.depcache.json', 'r') as f:
					self.cache = json.load(f)
			else:
				self.cache = {}

	def _save(self):
		with directory(os.path.dirname(os.path.abspath(__file__))):
			with open('.depcache.json', 'w') as f:
				json.dump(self.cache, f)

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
		for k, v in self.cache.iteritems():
			print('{}{}'.format(ANSI.decorate('[failed] ', ANSI.COLOR['red']) if not v else '', k))


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

	def _install_easy_install(self):
		with directory(os.path.dirname(os.path.abspath(__file__))):  # This has to be done relative to strap.py
			self._shell('python lib/ez_setup.py')

	@module(lambda _: shell('easy_install --version', silent=True) == 0, _install_easy_install)
	def easy_install(self, command):
		self._shell('easy_install {}'.format(command))
		return self

	def _install_pip(self):
		with directory(os.path.dirname(os.path.abspath(__file__))):  # This has to be done relative to strap.py
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


def _cache(action):
	getattr(strap._depcache, action)()

def cache_done(err):
	strap._depcache._save()

def _list():
	from inspect import getmembers, isfunction
	with directory(os.getcwd()):
		if not os.path.isfile(STRAP_FILE):
			raise Exception('Missing configuration file "{}"!'.format(STRAP_FILE))
		config = imp.load_source('strapme', os.path.abspath(STRAP_FILE))
		d = {e[0]: e[1] for e in getmembers(config, isfunction) if not e[0].startswith('_')}
		col_width = max(len(k) for k, v in d.iteritems()) + 2
		for k, v in d.iteritems():
			print('{}{}'.format(k.ljust(col_width), v.__doc__ or ''))

def list_done(err):
	if err:
		print(err, file=sys.stderr)

def done(err):
	cache_done(err)
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

@app.cmd(help='Manage strap\'s dependency cache')
@app.cmd_arg('action', choices=['clean', 'list'])
def cache(action, callback=cache_done):
	funwrap(_cache, {'action': action}, False, callback)

@app.cmd(name='list', help='List the tasks defined in a project\'s strapme file')
def list_tasks(callback=list_done):
	funwrap(_list, {}, False, callback)

def main():
	if len(sys.argv) == 1:
		sys.argv.append('run')  # Run default task
	try:
		app.run()
	except ClipExit as e:
		pass

if __name__ == '__main__':
	main()
