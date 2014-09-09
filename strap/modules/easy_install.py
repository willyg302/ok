def check():
	return shell('easy_install --version', silent=True) == 0

def install():
	with strap_directory():  # This has to be done relative to strap.py
		strap._shell('python lib/ez_setup.py')

def run(command):
	strap._shell('easy_install {}'.format(command))
	return strap
