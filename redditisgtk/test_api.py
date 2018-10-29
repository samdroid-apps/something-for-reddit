import json
from unittest.mock import MagicMock

from redditisgtk import api


def test_is_special_sub():
    assert api.is_special_sub('/message/inbox')
    assert not api.is_special_sub('/r/something')
    assert api.is_special_sub('/user/somebody/hidden')

def build_fake_api(responses=None, is_anonymous=True):
    '''
    Responses is a dictionary of url -> resp

    If resp is a dict, it is returned as json

    If resp is a list, the item is popped and returned as json
    '''
    if responses is None:
        responses = {}

    session = MagicMock()
    def queue_message(msg, callback, user_data):
        url = msg.props.uri.to_string(True)

        msg.props = MagicMock()
        msg.props.status_code = 200

        resp = responses[url]
        if isinstance(resp, list):
            resp = resp.pop(0)
        data = bytes(json.dumps(resp), 'utf8')
        flat = MagicMock()
        flat.get_data.return_value = data
        msg.props.response_body.flatten.return_value = flat

        callback(session, msg, user_data)

    session.queue_message = queue_message
            
    token = MagicMock()
    token.wrap_path = lambda p: 'https://example.com' + p
    token.is_anonymous = is_anonymous
    return api.RedditAPI(session, token), session, token

def test_create_api():
    api, session, token = build_fake_api()
    assert api

def test_token_changed_gets_username():
    api, session, token = build_fake_api({
        '/subreddits/mine/subscriber?limit=100': {
            'data': {
                'children': [],
            },
        },
        '/api/v1/me': {
            'name': 'myname',
        },
    }, is_anonymous=False)
    assert token.set_user_name.called
    (name,), _ = token.set_user_name.call_args
    assert name == 'myname'

    token.user_name = 'something'
    assert api.user_name is token.user_name

def test_token_changed_to_annon():
    api, session, token = build_fake_api()
    assert api.user_name is token.user_name

def test_update_subscriptions():
    api, session, token = build_fake_api({
        '/subreddits/mine/subscriber?limit=100': {
            'data': {
                'children': [{
                    'data': {
                        'url': '/r/one',
                    },
                }],
            },
            'after': 'afterkey',
        },
        '/subreddits/mine/subscriber?limit=100&after=afterkey': {
            'data': {
                'children': [{
                    'data': {
                        'url': '/r/two',
                    },
                }],
            },
        },
    })
    api.subs_changed = MagicMock()

    api.update_subscriptions()
    assert api.user_subs == ['/r/one', '/r/two']
    assert api.lower_user_subs == ['/r/one', '/r/two']
    assert api.subs_changed.emit.called

def test_retry_on_401():
    api, session, token = build_fake_api({
        '/test': [
            {
                'error': 401,
            },
            {
                'win': True,
            },
        ],
    })

    done_cb = MagicMock()
    api.send_request('GET', '/test', done_cb)
    assert token.refresh.called
    (inner_cb,), _ = token.refresh.call_args
    inner_cb()
    assert done_cb.call_count == 1
    (data,), _ = done_cb.call_args
    assert data == {'win': True}


def test_bubble_error():
    api, session, token = build_fake_api({
        '/test': {'error': 403},
    })

    done_cb = MagicMock()
    api.request_failed = MagicMock()
    api.send_request('GET', '/test', done_cb)
    assert done_cb.call_count == 0

    assert api.request_failed.emit.called
    (args, msg), _ = api.request_failed.emit.call_args
    assert msg == 'Reddit Error: 403'


def test_callback_user_data():
    api, session, token = build_fake_api({
        '/test': {'win': True},
    })

    done_cb = MagicMock()
    ud = 'something'
    api.send_request('GET', '/test', done_cb, user_data=ud)
    assert done_cb.call_count == 1
    (data, ud_ref), _ = done_cb.call_args
    assert data == {'win': True}
    assert ud_ref is ud

def test_load_more(datadir):
    with open(datadir / 'api__load-more.json') as f:
        j = json.load(f)
    api, session, token = build_fake_api({
        '/api/morechildren?api_type=json&children=a%2Cb&link_id=link_name': (
            j['input']),
    })

    done_cb = MagicMock()
    api.load_more('link_name', {'children': ['a', 'b']}, done_cb)
    assert done_cb.call_count == 1
    (data,), _ = done_cb.call_args
    assert data == j['output']
