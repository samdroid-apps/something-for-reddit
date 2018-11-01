import json
import pytest
import shutil
from unittest.mock import MagicMock, patch

from redditisgtk import api 
from redditisgtk import identity

def build_identity_controller(path: str = None):
    if path is None:
        path = '/fake/wow-this-is-a-fake-path'

    session = MagicMock()
    ic = identity.IdentityController(session, path)
    return ic, session


def test_identity_controller_create():
    ic, session = build_identity_controller()


def test_identity_controller_default_active():
    ic, session = build_identity_controller()
    assert isinstance(ic.active_token, api.TokenManager)


def test_identity_controller_load_file(datadir):
    with patch('redditisgtk.api.OAuthTokenManager') as FakeTokenManager:
        ic, session = build_identity_controller(
                path=datadir / 'identity--load.json')

        assert isinstance(ic.active_token, MagicMock)

        token = FakeTokenManager.call_args[1]['token']
        assert token['access_token'] == 'AT'
        assert token['username'] == 'myname'


def test_token_changed(datadir, tempdir):
    path = tempdir / 'i.json'
    shutil.copy(datadir / 'identity--load.json', path)

    with patch('redditisgtk.api.OAuthTokenManager') as FakeTokenManager:
        ic, session = build_identity_controller(path=path)
        ic.token_changed = MagicMock()

        ic.active_token.serialize.return_value = {'win': 1}

        assert ic.active_token.value_changed.connect.called
        (callback,), _ = ic.active_token.value_changed.connect.call_args

        callback(ic.active_token)
        assert ic.token_changed.emit.called

        with open(path) as f:
            data = json.load(f)
            assert data['active'] == 'testid'
            assert data['tokens']['testid'] == {'win': 1}


def test_identity_controller_delete(datadir, tempdir):
    path = tempdir / 'i.json'
    shutil.copy(datadir / 'identity--load.json', path)

    with patch('redditisgtk.api.OAuthTokenManager') as FakeTokenManager:
        ic, session = build_identity_controller(path=path)
        ic.token_changed = MagicMock()

        ic.remove_account('testid')

        assert ic.token_changed.emit.called
        assert isinstance(ic.active_token, api.AnonymousTokenManager)

        with open(path) as f:
            data = json.load(f)
            assert data['active'] == None
            assert data['tokens'] == {}
