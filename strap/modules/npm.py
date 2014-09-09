def check():
	return shell('npm --version', silent=True) == 0

def install():
	raise StrapException('Installation must be done manually.\nPlease visit http://nodejs.org/ for installation instructions.')

def run(command):
	strap._shell('npm {}'.format(command))
	return strap
