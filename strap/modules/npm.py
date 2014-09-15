def check():
	return strap.ping('npm --version')

def install():
	raise StrapException('Installation must be done manually.\nPlease visit http://nodejs.org/ for installation instructions.')

def run(command):
	strap._shell('npm {}'.format(command))
	return strap
