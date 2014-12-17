import unittest
from mock import patch, mock_open

from ok import ok


class Stream(object):
	def __init__(self):
		self._writes = []

	def write(self, message):
		self._writes.append(message)


class BaseTest(unittest.TestCase):
	'''Base class for tests in this file.
	'''

	def setUp(self):
		self.out, self.err = self.embed()

	def embed(self):
		out, err = Stream(), Stream()
		ok.clip.clip_globals.set_stdout(out)
		ok.clip.clip_globals.set_stderr(err)
		return out, err


class TestOk(BaseTest):

	def test_version(self):
		ok.main('--version')
		self.assertTrue(self.out._writes[0].startswith('ok version'))


class TestInit(BaseTest):

	@patch('ok.ok.run')
	@patch('ok.ok.OkAPI.shell')
	def test_clone(self, shell, run):
		ok.init('gh:owner/repo', None)
		shell.assert_called_with('git clone git@github.com:owner/repo.git repo', force_global=True)
		run.assert_called_with(['install'], 'repo', False)
		ok.init('gh:owner/repo', 'somedir')
		shell.assert_called_with('git clone git@github.com:owner/repo.git somedir', force_global=True)
		run.assert_called_with(['install'], 'somedir', False)

	@patch('ok.ok.run')
	@patch('ok.ok.shutil.copytree')
	def test_copy(self, copy, run):
		ok.init('somedir', None)
		self.assertFalse(copy.called)
		run.assert_called_with(['install'], 'somedir', False)
		ok.init('somedir', 'otherdir', silent=True)
		copy.assert_called_with('somedir', 'otherdir')
		run.assert_called_with(['install'], 'otherdir', True)


class TestRun(BaseTest):

	pass


class TestModules(BaseTest):

	@patch('ok.ok.clip.confirm')
	@patch('ok.ok.ModuleCache.clean')
	def test_clean(self, clean, confirm):
		ok.main('modules clean')
		self.assertTrue(confirm.call_args[1]['abort'])
		self.assertFalse(ok.okapi.notify_on_close)
		self.assertTrue(clean.called)

	@patch('ok.ok.ModuleCache.list_available')
	@patch('ok.ok.ModuleCache.list')
	def test_list(self, downloaded, available):
		ok.main('modules list')
		self.assertTrue(downloaded.called)
		ok.main('modules list --available')
		self.assertTrue(available.called)

	@patch('ok.ok.ModuleCache.sync')
	def test_sync(self, sync):
		ok.main('modules sync')
		self.assertTrue(sync.called)


class TestList(BaseTest):

	pass


class TestModuleCache(BaseTest):

	@patch('ok.ok.utils.fetch_github_file')
	@patch('ok.ok.utils.ok_directory')
	@patch('ok.ok.os.path.isfile', side_effect=[False, False])
	def test_loading_no_files(self, isfile, ok_directory, fetch):
		with patch('__builtin__.open', mock_open(read_data='["yo!"]'), create=True) as m:
			mc = ok.ModuleCache()
			self.assertEqual(mc._cache, {})
			fetch.assert_called_with({
				'user': 'willyg302',
				'repo': 'ok-modules',
				'commit': 'master',
				'filepath': 'registry.json'
			}, 'modules/.registry.json')
			m.assert_called_once_with('modules/.registry.json', 'r')
			self.assertEqual(mc._registry, ['yo!'])

	@patch('ok.ok.utils.ok_directory')
	@patch('ok.ok.os.path.isfile', side_effect=[True, True])
	def test_loading_files(self, isfile, ok_directory):
		with patch('__builtin__.open', mock_open(read_data='["yo!"]'), create=True) as m:
			mc = ok.ModuleCache()
			self.assertEqual(mc._cache, ['yo!'])
			self.assertEqual(mc._registry, ['yo!'])
