from pathlib import Path
from tempfile import TemporaryDirectory

from pytest import fixture


@fixture
def datadir() -> Path:
    '''
    Fixture that gives the path of the data directory
    '''
    return Path(__file__).absolute().parent / 'tests-data'

@fixture
def tempdir() -> Path:
    '''
    Fixture that gives you the path of a new temporary directory
    '''
    with TemporaryDirectory() as dirname:
        yield Path(dirname).absolute()
