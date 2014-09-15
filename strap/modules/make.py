def check():
	return strap.ping('make --version')

def install():
	raise StrapException('Installation must be done manually.\nPlease visit http://www.gnu.org/software/make/ for installation instructions.')

def run(command=None):
	strap._shell('make{}'.format('' if command is None else " " + command))
	return strap
