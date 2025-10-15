import pytest

from aeghash.utils.retry import RetryConfig, retry


def test_retry_success():
    calls = []

    @retry(RetryConfig(attempts=3, initial_delay=0.01))
    def func():
        calls.append(1)
        return "ok"

    assert func() == "ok"
    assert len(calls) == 1


def test_retry_failure():
    calls = []

    @retry(RetryConfig(attempts=3, initial_delay=0.01))
    def func():
        calls.append(1)
        raise ValueError("fail")

    with pytest.raises(ValueError):
        func()
    assert len(calls) == 3
