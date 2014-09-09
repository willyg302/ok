import os
import contextlib
import imp

from subprocess import call, STDOUT


__all__ = [
	'directory', 'strap_directory', 'get_strapme', 'get_module', 'normalize_path', 'shell',
	'StrapException', 'ANSI'
]


STRAP_FILE = 'strapme.py'

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

@contextlib.contextmanager
def strap_directory():
	with directory(os.path.dirname(os.path.abspath(__file__))):
		yield

def get_strapme(dir=os.getcwd()):
	with directory(dir):
		if not os.path.isfile(STRAP_FILE):
			raise Exception('Missing configuration file "{}"!'.format(STRAP_FILE))
		return imp.load_source('strapme', os.path.abspath(STRAP_FILE))

def get_module(name):
	with strap_directory():
		return imp.load_source(name, os.path.abspath(os.path.join('modules', '{}.py'.format(name))))

def normalize_path(path):
	return path.replace('/', os.sep)

def shell(command, silent=False):
	if silent:
		with open(os.devnull, 'w') as fnull:
			return call(command, stdout=fnull, stderr=STDOUT, shell=True)
	else:
		return call(command, shell=True)


class StrapException(Exception):
	pass


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
