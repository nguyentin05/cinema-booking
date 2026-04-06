from app.utils import get_redis


def test_redis_is_properly_mocked(test_app):
    redis_client = get_redis()

    assert type(redis_client).__name__ == 'FakeRedis'


def test_redis_basic_set_get(test_app):
    redis_client = get_redis()

    redis_client.set('greeting', 'hello from Ximofam')

    value = redis_client.get('greeting')
    assert value == 'hello from Ximofam'
