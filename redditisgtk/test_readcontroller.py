from unittest.mock import MagicMock, patch

from redditisgtk import readcontroller

@patch('os.makedirs')
@patch('os.path.isdir', return_value=False)
def test_get_data_file_path(isdir, makedirs):
    path = readcontroller.get_data_file_path('name')
    assert path.endswith('name')
    assert path.startswith('/')
    assert makedirs.called


@patch('os.makedirs')
@patch('os.path.isdir', return_value=True)
def test_get_data_file_path_no_create(isdir, makedirs):
    path = readcontroller.get_data_file_path('name')
    assert not makedirs.called


def test_readcontroller_load(tmpdir):
    path = tmpdir / 'read'
    with open(path, 'w') as f:
        f.write('a1\na2')
    ctrl = readcontroller.ReadController(data_path=path)
    assert ctrl.is_read('a1')
    assert ctrl.is_read('a2')
    assert not ctrl.is_read('b1')

    ctrl.read('b1')
    assert ctrl.is_read('b1')

    ctrl.save()
    with open(path) as f:
        assert sorted(f.read().splitlines()) == ['a1', 'a2', 'b1']
