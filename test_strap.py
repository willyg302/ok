import unittest
import sys
import shlex

from subprocess import Popen, PIPE

from strap import strap


def capture(command):
	p = Popen(shlex.split(command), stdout=PIPE, stderr=PIPE)
	return p.communicate()

def call_strap(args):
	return capture('python strap {}'.format(args))


class TestStrap(unittest.TestCase):

	def setUp(self):
		strap.strap = strap.Strap()

	def test_version(self):
		_, err = call_strap('--version')
		self.assertTrue(err.startswith('strap version'))

	def test_help(self):
		self.assertTrue(call_strap('-h')[0].startswith('usage: strap'))
		for e in ['init', 'run', 'cache', 'list']:
			self.assertTrue(call_strap('{} -h'.format(e))[0].startswith('usage: {}'.format(e)))


if __name__ == '__main__':
	unittest.main()
