def check():
	return strap.ping('bower --version')

def install():
	strap.npm('install -g bower')

def run(command, root='.'):
	with strap.root(root):
		strap._shell('bower {}'.format(command))
	return strap
