def test_redis_is_properly_mocked(redis_client):
    assert type(redis_client).__name__ == 'FakeRedis'


def test_redis_basic_set_get(redis_client):
    redis_client.set('greeting', 'hello from Ximofam')

    value = redis_client.get('greeting')
    assert value == 'hello from Ximofam'
