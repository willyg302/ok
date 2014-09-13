import unittest
import sys

from cStringIO import StringIO

from strap import strap


# http://stackoverflow.com/questions/16571150/how-to-capture-stdout-output-from-a-python-function-call
class Capturing(list):

	def __enter__(self):
		self._stdout = sys.stdout
		sys.stdout = self._ioout = StringIO()
		return self

	def __exit__(self, *args):
		self.extend(self._ioout.getvalue().splitlines())
		sys.stdout = self._stdout


class TestStrap(unittest.TestCase):

	def setUp(self):
		strap.strap = strap.Strap()

	def test_version(self):
		with Capturing() as output:
			strap.cache('list')
		self.assertIsInstance(output, list)


if __name__ == '__main__':
	unittest.main()
