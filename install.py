import os
import urllib

deps = {
	'strap/deps/clip.py': {
		'user': 'willyg302',
		'repo': 'clip.py',
		'commit': '5d032317646379ffb0d8fec4a11949478707dc5e',
		'filepath': 'clip.py'
	},
	'strap/deps/giturl.py': {
		'user': 'willyg302',
		'repo': 'giturl',
		'commit': '51d17f1698ce817123174c6a90f2c1f4ec43c9dd',
		'filepath': 'giturl.py'
	}
}

GIT_URL = 'https://raw.githubusercontent.com/{user}/{repo}/{commit}/{filepath}'

for dest, source in deps.iteritems():
	urllib.urlretrieve(GIT_URL.format(**source), dest.replace('/', os.sep))
