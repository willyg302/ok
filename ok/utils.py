import os
import contextlib
import imp
import urllib

from subprocess import call, STDOUT


CONFIG = 'okfile'


class OkException(Exception):
	pass


########################################
# DIRECTORY/FILE UTILS
########################################

def normalize_path(path):
	return path.replace('/', os.sep)

@contextlib.contextmanager
def directory(path):
	'''Context manager for changing the current working directory'''
	path = normalize_path(path)
	if not os.path.isdir(path):
		raise IOError('"{}" is not a valid directory!'.format(path))
	prev_cwd = os.getcwd()
	os.chdir(path)
	try:
		yield
	finally:
		os.chdir(prev_cwd)

@contextlib.contextmanager
def ok_directory():
	'''Context manager for working relative to ok'''
	with directory(os.path.dirname(os.path.abspath(__file__))):
		yield

def in_ok(f):
	'''Decorator to execute a function relative to ok'''
	def decorator(*args, **kwargs):
		with ok_directory():
			return f(*args, **kwargs)
	return decorator

def load_file(name, path):
	'''Dynamically load a Python file from disk'''
	if not os.path.isfile(path):
		raise OkException('Unable to load file "{}"!'.format(path))
	return imp.load_source(name, os.path.abspath(path))

def load_config():
	'''Load a project's config file'''
	return load_file(CONFIG, '{}.py'.format(CONFIG))

def load_module(name):
	'''Load an ok module from the modules directory'''
	with ok_directory():
		return load_file(name, os.path.join('modules', '{}.py'.format(name)))

def ping_directory(path):
	'''Create a directory if it does not already exist'''
	try:
		os.makedirs(path)
	except OSError:
		pass


########################################
# MISC UTILS
########################################

def shell(command, silent=False):
	command = normalize_path(command)  # For commands with dirs in them
	if silent:
		with open(os.devnull, 'w') as fnull:
			return call(command, stdout=fnull, stderr=STDOUT, shell=True)
	else:
		return call(command, shell=True)

GITHUB_FILE_URL = 'https://raw.githubusercontent.com/{user}/{repo}/{commit}/{filepath}'

# @TODO: Handle possible errors. ok should short-circuit if anything goes wrong here
def fetch_github_file(source, dest):
	urllib.urlretrieve(GITHUB_FILE_URL.format(**source), normalize_path(dest))


########################################
# ANSI ESCAPE CODES
########################################

class ANSI(object):
	ESCAPE = '\033[{}m'
	END = ESCAPE.format('0')

	BOLD = '1'
	ITALIC = '3'
	UNDERLINE = '4'

	COLOR = {e: str(30 + i) for i, e in enumerate(['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'])}

	@classmethod
	def decorate(cls, s, styles):
		if isinstance(styles, (list, tuple)):
			styles = ';'.join(styles)
		return '{}{}{}'.format(cls.ESCAPE.format(styles), s, cls.END)
