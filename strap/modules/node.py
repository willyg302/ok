def check():
	return strap.ping('node --version')

def install():
	raise StrapException('Installation must be done manually.\nPlease visit http://nodejs.org/ for installation instructions.')

def run(command, module=False):
	if module:
		strap._shell('node_modules/.bin/{}'.format(command))
	else:
		strap._shell('node {}'.format(command))
	return strap
