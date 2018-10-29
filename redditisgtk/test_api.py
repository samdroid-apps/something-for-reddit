import json
from unittest.mock import MagicMock

from redditisgtk import api


def test_is_special_sub():
    assert api.is_special_sub('/message/inbox')
    assert not api.is_special_sub('/r/something')
    assert api.is_special_sub('/user/somebody/hidden')

def build_fake_api(responses=None):
    if responses is None:
        responses = {}

    session = MagicMock()
    def queue_message(msg, callback, user_data):
        url = msg.props.uri.to_string(True)

        msg.props = MagicMock()
        msg.props.status_code = 200

        data = bytes(json.dumps(responses[url]), 'utf8')
        flat = MagicMock()
        flat.get_data.return_value = data
        msg.props.response_body.flatten.return_value = flat

        callback(session, msg, user_data)

    session.queue_message = queue_message
            
    ic = MagicMock()
    return api.RedditAPI(session, ic), session, ic

def test_create_api():
    api, session, ic = build_fake_api()
    assert ic.token_changed.connect.called
    assert api

def test_token_changed_gets_username():
    api, session, ic = build_fake_api({
        '/subreddits/mine/subscriber?limit=100': {
            'data': {
                'children': [],
            },
        },
        '/api/v1/me': {
            'name': 'myname',
        },
    })
    assert ic.token_changed.connect.called
    token_changed_cb = ic.token_changed.connect.call_args[0][0]

    token_changed_cb(ic, {'access_token': 'tok'})
    assert api.user_name == 'myname'

def test_token_changed_to_annon():
    api, session, ic = build_fake_api()
    assert ic.token_changed.connect.called
    token_changed_cb = ic.token_changed.connect.call_args[0][0]

    token_changed_cb(ic, None)
    assert api.user_name == None
