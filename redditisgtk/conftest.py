import os
import json
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


def assert_matches_snapshot(name: str, data: dict):
    '''
    Checks that the data matches the data stored in the snapshot.

    If the snapshot does not exist, it creates a snapshot with the passed data
    '''
    snap_dir = Path(__file__).absolute().parent / 'tests-data' / 'snapshots'
    path = snap_dir / (name + '.json')

    if path.exists():
        with open(path) as f:
            expected = json.load(f)
        assert data == expected
    else:  # pragma: no cover
        if 'CI' in os.environ:
            raise Exception('Snapshot not found in CI environment')

        with open(path, 'w') as f:
            json.dump(data, f, indent=2, sort_keys=True)
