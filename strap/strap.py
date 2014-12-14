from __future__ import print_function

import os
import sys
import shutil
import contextlib
import json

from deps import clip
from deps.giturl import *
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
			# Load a list of available modules
			self.available_modules = [e[:-3] for e in os.listdir('modules')]
		self.loaded_modules = {}

	def _save(self):
		with strap_directory():
			with open('.depcache.json', 'w') as f:
				json.dump(self.cache, f)

	def close(self):
		if self.save_on_close:
			self._save()

	def load(self, module_name):
		if module_name in self.loaded_modules:
			return self.loaded_modules[module_name]
		module = get_module(module_name)

		# Shim some stuff into the module
		# @TODO: There has got to be a better (but still explicit) way...
		setattr(module, 'strap', strap)
		setattr(module, 'StrapException', StrapException)
		setattr(module, 'strap_directory', strap_directory)
		setattr(module, 'normalize_path', normalize_path)
		setattr(module, 'log', log)

		if not self.cache.get(module_name):
			log('Checking whether {} is installed...'.format(module_name), important=False)
			if not module.check():
				log('{} not installed, installing now...'.format(module_name))
				try:
					module.install()
				except Exception as e:
					self.cache[module_name] = False
					raise StrapException('Unable to install module {}: {}'.format(module_name, e.message))
			self.cache[module_name] = True
		self.loaded_modules[module_name] = module
		return module

	def clean(self):
		self.cache = {}
		log('Dependency cache successfully cleaned')

	def list(self):
		if not self.cache:
			log('Cache is empty')
			return
		for k in sorted(self.cache):
			print('{}{}'.format(ANSI.decorate('[failed] ', ANSI.COLOR['red']) if not self.cache[k] else '', k))


class Strap(object):

	def __init__(self):
		self._env = None
		self._depcache = DependencyCache()
		self.silent = False
		self.notify_on_close = True

	def __getattr__(self, name):
		if name in self._depcache.available_modules:
			def wrapped_f(*args, **kwargs):
				return self._depcache.load(name).run(*args, **kwargs)
			return wrapped_f
		raise AttributeError('Method "{}" not recognized!'.format(name))

	def _close(self, err):
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

	@contextlib.contextmanager
	def root(self, path):
		with directory(normalize_path(path)):
			yield

	def freeze(self, filename='requirements.txt'):
		self.pip('freeze > {}'.format(filename))

	def ping(self, command):
		return shell(command, silent=True) == 0

	def run(self, task):
		if isinstance(task, (list, tuple)):
			for t in task:
				self.run(t)
		else:
			if hasattr(task, '__call__'):
				log('Running task {}'.format(ANSI.decorate(task.__doc__ or task.__name__, [ANSI.BOLD, ANSI.COLOR['cyan']])))
				task()
			else:
				# First check whether we can offload task to a module
				fname, fargs = task.partition(' ')[::2]
				if fname in self._depcache.available_modules:
					getattr(self, fname)(fargs)
				else:
					self._shell(task)
		return self


strap = Strap()


def log(message, important=True):
	if important or not strap.silent:
		print('{} {}'.format(ANSI.decorate('[strap]', [ANSI.BOLD, ANSI.COLOR['green']]), message))

# Deletes [dir] if it exists and the user approves
def verify_write_directory(dir):
	if os.path.isdir(dir):
		clip.confirm('The directory "{}" already exists! Overwrite?'.format(dir), abort=True)
		shutil.rmtree(dir)

# Clones a project from a remote URI [source] to [dest]
def clone(source, dest):
	verify_write_directory(dest)
	log('Cloning git repo "{}" to "{}"...'.format(source, dest))
	strap._shell('git clone {} {}'.format(source, dest), force_global=True)

# Copies a project from a local directory [source] to [dest]
def copy(source, dest):
	if source == dest:
		return
	verify_write_directory(dest)
	log('Copying directory "{}" to "{}"...'.format(source, dest))
	shutil.copytree(source, dest)


app = clip.App()

def print_version(value):
	clip.exit('strap version {}'.format(__version__))

@app.main(name='strap')
@clip.flag('--version', callback=print_version, hidden=True, help='Print the version')
@clip.flag('-s', '--silent', inherit_only=True)
def main():
	pass

@main.subcommand(inherits=['-s'], description='Clone a project and run its install task')
@clip.arg('source', required=True, help='The directory or repo to clone from')
@clip.opt('-d', '--dest', help='Where to initialize the project')
def init(source, dest, silent=False):
	strap.silent = silent
	log('Fetching project')
	g = GitURL(source)
	fun, s, d = (clone, g.to_ssh(), dest or g.repo) if g.valid else (copy, source, dest or source)
	fun(s, d)
	run(['install'], d, silent)

@main.subcommand(inherits=['-s'], description='Run one or more tasks defined in a project\'s strapme file')
@clip.arg('tasks', nargs=-1, default=['default'], help='The task(s) to run')
@clip.opt('-d', '--dir', default=os.getcwd(), help='Optional path to execute the tasks from')
def run(tasks, dir, silent=False):
	strap.silent = silent
	with directory(dir):
		config = get_strapme()
		log('Running tasks on {}'.format(config.project if hasattr(config, 'project') else os.path.basename(dir)))
		setattr(config, 'strap', strap)
		for task in tasks:
			if not hasattr(config, task):
				log('"{}" not a valid task, skipping!'.format(task))
				continue
			strap.run(getattr(config, task))
	log('All tasks complete!')

@main.subcommand(description='Manage strap\'s dependency cache')
def cache():
	strap.notify_on_close = False

@cache.subcommand(name='clean')
def cache_clean():
	strap._depcache.clean()

@cache.subcommand(name='list')
def cache_list():
	strap._depcache.list()

@main.subcommand(name='list', description='List the tasks defined in a project\'s strapme file')
def list_tasks():
	strap.notify_on_close = False
	from inspect import getmembers, isfunction
	d = {e[0]: e[1] for e in getmembers(get_strapme(), isfunction) if not e[0].startswith('_')}
	col_width = max(len(k) for k, v in d.iteritems()) + 2
	for k in sorted(d):
		print('{}{}'.format(k.ljust(col_width), d[k].__doc__ or ''))


def start():
	if len(sys.argv) == 1:
		sys.argv.append('run')  # Run default task
	err = None
	try:
		app.run()
	except clip.ClipExit:
		# Parser-level exception, such as help/version or unrecognized argument
		strap.notify_on_close = False
	except Exception as e:
		err = e
		print(e, file=sys.stderr)
	finally:
		strap._close(err)

if __name__ == '__main__':
	start()
