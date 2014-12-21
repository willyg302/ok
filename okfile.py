def test():
	with ok.virtualenv('env'):
		ok.run('python -m unittest discover tests')

def install():
	with ok.virtualenv('env'):
		ok.pip('install mock').freeze()

def default():
	ok.run(test)
