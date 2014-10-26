import unittest
import sys
import shlex

from subprocess import Popen, PIPE
from mock import patch

from strap import strap


def capture(command):
	p = Popen(shlex.split(command), stdout=PIPE, stderr=PIPE)
	return p.communicate()

def call_strap(args):
	return capture('python strap {}'.format(args))


class TestStrap(unittest.TestCase):

	def test_version(self):
		_, err = call_strap('--version')
		self.assertTrue(err.startswith('strap version'))

	def test_help(self):
		self.assertTrue(call_strap('-h')[0].startswith('usage: strap'))
		for e in ['init', 'run', 'cache', 'list']:
			self.assertTrue(call_strap('{} -h'.format(e))[0].startswith('usage: {}'.format(e)))

	@patch('strap.strap.run')
	@patch('strap.strap.Strap._shell')
	def test_clone(self, shell, run):
		strap.init('gh:owner/repo', None)
		shell.assert_called_with('git clone git@github.com:owner/repo.git repo', force_global=True)
		run.assert_called_with(['install'], 'repo', False)
		strap.init('gh:owner/repo', 'somedir')
		shell.assert_called_with('git clone git@github.com:owner/repo.git somedir', force_global=True)
		run.assert_called_with(['install'], 'somedir', False)

	@patch('strap.strap.run')
	@patch('strap.strap.shutil.copytree')
	def test_copy(self, copy, run):
		strap.init('somedir', None)
		self.assertFalse(copy.called)
		run.assert_called_with(['install'], 'somedir', False)
		strap.init('somedir', 'otherdir', silent=True)
		copy.assert_called_with('somedir', 'otherdir')
		run.assert_called_with(['install'], 'otherdir', True)


if __name__ == '__main__':
	unittest.main()
