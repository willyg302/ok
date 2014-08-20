import os
import contextlib


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

def normalize_path(path):
	return path.replace('/', os.sep)


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
