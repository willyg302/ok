def test():
	with strap.virtualenv('env'):
		strap.run('python test_strap.py')

def install():
	with strap.virtualenv('env'):
		strap.pip('install mock').freeze()

def default():
	strap.run(test)
