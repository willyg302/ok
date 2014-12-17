import os
import sys
import shutil
import contextlib
import json

import utils
from deps import clip
from deps.giturl import *


__version__ = '0.5.0'


########################################
# MODULE CACHE
########################################

class ModuleCache:
	'''Manages ok modules.

	Modules may be in one of 3 states:

	  - Not downloaded, meaning they must be grabbed from the registry at
	    https://github.com/willyg302/ok-modules
	  - Downloaded, but not verified (a module is verified when its
	  	installation has been completed successfully)
	  - Verified -- this is the only state in which a module may be called

	All downloaded modules live in the modules/ directory, along with a
	.cache.json file that keeps track of the state of downloaded modules.
	The state is a simple boolean, True if verified.

	The .cache.json file is law, meaning that even if a module exists in the
	modules/ directory, if it is not also in .cache.json then it is considered
	"not downloaded" and must be grabbed from the registry again.

	There is also a .registry.json file that mirrors the registry.json file in
	the registry. If a module is not in the registry, then it does not exist.
	It's a good idea to sync the cache every once in a while to update the
	.registry.json.
	'''

	def __init__(self):
		# Just make sure the modules/ directory actually exists
		with utils.ok_directory():
			utils.ping_directory('modules')
		self._cache_file = utils.normalize_path('modules/.cache.json')
		self._registry_file = utils.normalize_path('modules/.registry.json')
		self._load_cache()
		self._load_registry()
		self._loaded_modules = {}  # In-memory cache of loads on THIS run

	@utils.in_ok
	def _load_cache(self):
		if os.path.isfile(self._cache_file):
			with open(self._cache_file, 'r') as f:
				self._cache = json.load(f)
		else:
			self._cache = {}

	@utils.in_ok
	def _load_registry(self):		
		# If it doesn't exist yet, download it
		if not os.path.isfile(self._registry_file):
			self.sync()
		with open(self._registry_file, 'r') as f:
			self._registry = json.load(f)

	@utils.in_ok
	def _save_cache(self):
		with open(self._cache_file, 'w') as f:
			json.dump(self._cache, f)

	@utils.in_ok
	def _download(self, source, dest):
		utils.fetch_github_file({
			'user': 'willyg302',
			'repo': 'ok-modules',
			'commit': 'master',
			'filepath': source
		}, dest)

	def close(self):
		self._save_cache()

	def exists(self, module_name):
		return module_name in self._registry

	def load(self, module_name):
		# If it has been loaded already, just return it!
		if module_name in self._loaded_modules:
			return self._loaded_modules[module_name]

		# If it's not in the cache, download it
		if module_name not in self._cache:
			module_path = 'modules/{}.py'.format(module_name)
			self._download(module_path, module_path)
			# Just downloaded, still have to verify
			self._cache[module_name] = False

		module = utils.load_module(module_name)
		# Shim some stuff into the module
		# @TODO: There has got to be a better (but still explicit) way...
		setattr(module, 'ok', okapi)
		setattr(module, 'utils', utils)

		# If it's not verified, try to verify it
		if not self._cache[module_name]:
			okapi.log('Checking whether {} is installed...'.format(module_name), important=False)
			if not module.check():
				okapi.log('{} not installed, installing now...'.format(module_name))
				try:
					module.install()
				except Exception as e:
					raise utils.OkException('Unable to install module {}: {}'.format(module_name, e.message))
			self._cache[module_name] = True

		# At this point we know it exists and is loaded, so...
		self._loaded_modules[module_name] = module
		return module

	def clean(self):
		self._cache = {}
		okapi.log('Module cache successfully cleaned')

	def list(self):
		if not self._cache:
			okapi.log('No modules found')
			return
		for k in sorted(self._cache):
			clip.echo('{}{}'.format('' if self._cache[k] else utils.ANSI.decorate('[failed] ', utils.ANSI.COLOR['red']), k))

	def list_available(self):
		clip.echo('\n'.join(self._registry))

	def sync(self):
		self._download('registry.json', self._registry_file)


########################################
# ok API CLASS
########################################

class OkAPI(object):
	'''Defines an "API" for ok that can be shimmed into modules/config.
	'''

	def __init__(self):
		self.env = None
		self.module_cache = ModuleCache()
		self.silent = False
		self.notify_on_close = True

	def __getattr__(self, name):
		if self.module_cache.exists(name):
			def wrapped_f(*args, **kwargs):
				return self.module_cache.load(name).run(*args, **kwargs)
			return wrapped_f
		raise AttributeError('Method "{}" not recognized!'.format(name))

	def close(self, err):
		self.module_cache.close()
		if self.notify_on_close:
			status, color = ('There were errors.', 'red') if err else ('No error!', 'green')
			self.log('Complete! {}'.format(utils.ANSI.decorate(status, utils.ANSI.COLOR[color])))

	def shell(self, command, force_global=False):
		'''Wrapper around shell() that can invoke relative to a virtual environment'''
		if self.env and not force_global:
			command = '{}/{}'.format(self.env, command)
		try:
			ret = utils.shell(command, self.silent)
			if ret != 0:
				raise utils.OkException('Return value {} on call to {}'.format(ret, command))
		except KeyboardInterrupt:
			pass

	@contextlib.contextmanager
	def root(self, path):
		with utils.directory(path):
			yield

	def ping(self, command):
		return utils.shell(command, silent=True) == 0

	def run(self, task):
		if isinstance(task, (list, tuple)):
			for t in task:
				self.run(t)
		else:
			if hasattr(task, '__call__'):
				self.log('Running task {}'.format(utils.ANSI.decorate(task.__doc__ or task.__name__, [utils.ANSI.BOLD, utils.ANSI.COLOR['cyan']])))
				task()
			else:
				# First check whether we can offload task to a module
				fname, fargs = task.partition(' ')[::2]
				if self.module_cache.exists(fname):
					getattr(self, fname)(fargs)
				else:
					self.shell(task)
		return self

	def log(self, message, important=True):
		if important or not self.silent:
			clip.echo('{} {}'.format(utils.ANSI.decorate('[ok]', [utils.ANSI.BOLD, utils.ANSI.COLOR['green']]), message))


okapi = OkAPI()


########################################
# UTILITY FUNCTIONS
########################################

def verify_write_directory(dir):
	'''Deletes [dir] if it exists and the user approves'''
	if os.path.isdir(dir):
		clip.confirm('The directory "{}" already exists! Overwrite?'.format(dir), abort=True)
		shutil.rmtree(dir)

def clone(source, dest):
	'''Clones a project from a remote URI [source] to [dest]'''
	verify_write_directory(dest)
	okapi.log('Cloning git repo "{}" to "{}"...'.format(source, dest))
	okapi.shell('git clone {} {}'.format(source, dest), force_global=True)

def copy(source, dest):
	'''Copies a project from a local directory [source] to [dest]'''
	if source == dest:
		return
	verify_write_directory(dest)
	okapi.log('Copying directory "{}" to "{}"...'.format(source, dest))
	shutil.copytree(source, dest)


########################################
# COMMAND LINE APP
########################################

app = clip.App()

def print_version(value):
	clip.exit('ok version {}'.format(__version__))

@app.main()
@clip.flag('--version', callback=print_version, hidden=True, help='Print the version')
@clip.flag('-s', '--silent', inherit_only=True)
def ok():
	pass

@ok.subcommand(inherits=['-s'], description='Clone a project and run its install task')
@clip.arg('source', required=True, help='The directory or repo to clone from')
@clip.opt('-d', '--dest', help='Where to initialize the project')
def init(source, dest, silent=False):
	okapi.silent = silent
	okapi.log('Fetching project')
	g = GitURL(source)
	fun, s, d = (clone, g.to_ssh(), dest or g.repo) if g.valid else (copy, source, dest or source)
	fun(s, d)
	run(['install'], d, silent)

@ok.subcommand(inherits=['-s'], description='Run one or more tasks defined in a project\'s {}'.format(utils.CONFIG))
@clip.arg('tasks', nargs=-1, default=['default'], help='The task(s) to run')
@clip.opt('-d', '--dir', default=os.getcwd(), help='Optional path to execute the tasks from')
def run(tasks, dir=None, silent=False):
	if dir is None:
		dir = os.getcwd()
	okapi.silent = silent
	with utils.directory(dir):
		config = utils.load_config()
		okapi.log('Running tasks on {}'.format(config.project if hasattr(config, 'project') else os.path.basename(dir)))
		setattr(config, 'ok', okapi)
		for task in tasks:
			if not hasattr(config, task):
				okapi.log('"{}" not a valid task, skipping!'.format(task))
				continue
			okapi.run(getattr(config, task))
	okapi.log('All tasks complete!')

@ok.subcommand(description='Manage ok modules')
def modules():
	okapi.notify_on_close = False

@modules.subcommand(name='clean', description='[DANGER] Nuke your local cache of modules')
def modules_clean():
	clip.confirm('Are you sure you want to clean the module cache?', abort=True)
	okapi.module_cache.clean()

@modules.subcommand(name='list')
@clip.flag('-a', '--available', help='List all available modules in the registry')
def modules_list(available):
	if available:
		okapi.module_cache.list_available()
	else:
		okapi.module_cache.list()

@modules.subcommand(name='sync', description='Sync your module list from the online registry')
def modules_sync():
	okapi.module_cache.sync()

@ok.subcommand(name='list', description='List the tasks defined in a project\'s {}'.format(utils.CONFIG))
def list_tasks():
	okapi.notify_on_close = False
	from inspect import getmembers, isfunction
	d = {e[0]: e[1] for e in getmembers(utils.load_config(), isfunction) if not e[0].startswith('_')}
	col_width = max(len(k) for k, v in d.iteritems()) + 2
	for k in sorted(d):
		clip.echo('{}{}'.format(k.ljust(col_width), d[k].__doc__ or ''))


########################################
# MAIN METHOD
########################################

def main(args=sys.argv[1:]):
	err = None
	try:
		app.run(args or ['run'])
	except clip.ClipExit:
		# Parser-level exception, such as help/version or unrecognized argument
		okapi.notify_on_close = False
	except Exception as e:
		err = e
		clip.echo(e, err=True)
	finally:
		okapi.close(err)

if __name__ == '__main__':
	main()
