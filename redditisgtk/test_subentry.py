from redditisgtk import subentry


def test_clean_sub():
    assert subentry.clean_sub('') == '/'
    assert subentry.clean_sub('hello') == '/hello'
    assert subentry.clean_sub('/u/sam') == '/user/sam'


def test_format_sub_for_api_frontpage():
    assert subentry.format_sub_for_api('') == '/hot'
    assert subentry.format_sub_for_api('/') == '/hot'
    assert subentry.format_sub_for_api('/top') == '/top'

def test_format_sub_for_api_subreddit():
    assert subentry.format_sub_for_api('r/linux') == '/r/linux/hot'
    assert subentry.format_sub_for_api('/r/l/top?t=all') == '/r/l/top?t=all'

def test_format_sub_for_api_user():
    assert subentry.format_sub_for_api('/u/sam') == '/user/sam/overview'
    assert subentry.format_sub_for_api('/u/sam/up') == '/user/sam/up'
