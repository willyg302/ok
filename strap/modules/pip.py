def check():
	return strap.ping('pip --version')

def install():
	with strap_directory():  # This has to be done relative to strap.py
		strap.easy_install('--version')  # Ping to check if setuptools is installed
		strap._shell('python lib/get-pip.py')

def run(command):
	strap._shell('pip {}'.format(command))
	return strap
