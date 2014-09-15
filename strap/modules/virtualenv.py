import os
import contextlib
import platform


def check():
	return strap.ping('virtualenv --version')

def install():
	strap.pip('install virtualenv')

@contextlib.contextmanager
def run(path):
	try:
		path = normalize_path(path)

		# Check if our virtual environment is already created, and create if not
		log('Checking virtual environment')
		if not os.path.isdir(path):
			log('Creating virtual environment at {}...'.format(os.path.basename(path)))
			strap._shell('virtualenv {}'.format(path), force_global=True)

		strap._env = normalize_path('{}/{}'.format(path, 'Scripts' if platform.system() == 'Windows' else 'bin'))
		yield
	finally:
		strap._env = None
