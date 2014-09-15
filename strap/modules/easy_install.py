def check():
	return strap.ping('easy_install --version')

def install():
	with strap_directory():  # This has to be done relative to strap.py
		strap._shell('python lib/ez_setup.py')

def run(command):
	strap._shell('easy_install {}'.format(command))
	return strap
