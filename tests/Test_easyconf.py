import pytest

from ansible_collections.konono.easyconf.plugins.module_utils.easyconf import EasyConf
from typing import Any


@pytest.mark.parametrize(
    ('src', 'key', 'value', 'state'),
    (
        pytest.param('tests/test.yml',
            'config.person[3]', {'name': 'delta', 'gender': 'female', 'age': 21},
            'present', id='add'),
        pytest.param('tests/test.yml',
            'config.fruits', ['banana', 'peach', 'mikan'],
            'present', id='add'),
        pytest.param('tests/test.yml',
            'my.favorite.whiskey', 'kavalan',
            'present', id='add'),
        pytest.param('tests/test.yml',
            'config.person[-1]', {'name': 'yuri', 'gender': 'female', 'age': 21},
            'present', id='mod'),
        pytest.param('tests/test.yml',
            'config.fruits', 'orange',
            'present', id='mod'),
        pytest.param('tests/test.yml',
            'my.favorite.whiskey', 'macallan',
            'present', id='mod'),
        pytest.param('tests/test.yml',
            'config.person[3]', {"name": "yuri", "gender": "female", "age": 21},
            'absent', id='del'),
        pytest.param('tests/test.yml',
            'config.fruits', 'orange',
            'absent', id='del'),
        pytest.param('tests/test.yml',
            'my.favorite.whiskey', 'macallan',
            'absent', id='del'),
    ),
)

def test_easyconf(
    src: str,
    key: int,
    value: Any,
    state: str,
) -> None:
    '''Check if modified data result is correct.'''
    easyconf = EasyConf(path=src, state=state)
    conf = easyconf.update_config(key, value)
    if state == 'present':
        assert easyconf.match_config(key, conf) == value
    elif state == 'absent':
        assert easyconf.match_config(key, conf) == None
