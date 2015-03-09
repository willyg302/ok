import os

from ok import utils

deps = {
	'ok/deps/clip.py': {
		'user': 'willyg302',
		'repo': 'clip.py',
		'commit': 'master',
		'filepath': 'clip.py'
	},
	'ok/deps/giturl.py': {
		'user': 'willyg302',
		'repo': 'giturl',
		'commit': 'master',
		'filepath': 'giturl.py'
	},
	'ok/deps/antsy.py': {
		'user': 'willyg302',
		'repo': 'antsy',
		'commit': 'master',
		'filepath': 'antsy.py'
	}
}

COMPLETE_MESSAGE = '''Installation complete!

For best usage, please add the following aliases to your shell:

  - alias sudo='sudo '
  - alias ok='python {}/ok'

You can then call "ok" from the command line to use ok.
'''.format(os.getcwd())

def bootstrap():
	print('Bootstrapping dependencies...')
	for dest, source in utils.iteritems(deps):
		utils.fetch_github_file(source, dest)

def main():
	bootstrap()
	# At this point we have enough to run ok normally
	print('Installing ok...')
	from ok import ok
	ok.main('run install')
	print(COMPLETE_MESSAGE)

if __name__ == '__main__':
	main()
