# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Testing helpers.
"""

from contextlib import contextmanager

from ._config import configure, get_config
from .exceptions import DropEvent


__all__ = ["LogCapture", "capture_logs"]


class LogCapture(object):
    """
    Class for capturing log messages in its entries list.
    Generally you should use :func:`structlog.testing.capture_logs`,
    but you can use this class if you want to capture logs with other patterns.
    For example, using ``pytest`` fixtures::

        @pytest.fixture(scope='function')
        def log_output():
            return LogCapture()


        @pytest.fixture(scope='function', autouse=True)
        def configure_structlog(log_output):
            structlog.configure(
                processors=[log_output]
            )

        def test_my_stuff(log_output):
            do_something()
            assert log_output.entries == [...]

    .. versionadded:: 20.1.0
    """

    def __init__(self):
        self.entries = []

    def __call__(self, _, method_name, event_dict):
        event_dict["log_level"] = method_name
        self.entries.append(event_dict)
        raise DropEvent


@contextmanager
def capture_logs():
    """
    Context manager that appends all logging statements to its yielded list
    while it is active.


    Attention: this is **not** thread-safe!

    .. versionadded:: 20.1.0
    """
    cap = LogCapture()
    old_processors = get_config()["processors"]
    try:
        configure(processors=[cap])
        yield cap.entries
    finally:
        configure(processors=old_processors)


class ReturnLoggerFactory(object):
    r"""
    Produce and cache :class:`ReturnLogger`\ s.

    To be used with :func:`structlog.configure`\ 's `logger_factory`.

    Positional arguments are silently ignored.

    .. versionadded:: 0.4.0
    """

    def __init__(self):
        self._logger = ReturnLogger()

    def __call__(self, *args):
        return self._logger


class ReturnLogger(object):
    """
    Return the arguments that it's called with.

    >>> from structlog import ReturnLogger
    >>> ReturnLogger().msg("hello")
    'hello'
    >>> ReturnLogger().msg("hello", when="again")
    (('hello',), {'when': 'again'})

    Useful for testing.

    .. versionchanged:: 0.3.0
        Allow for arbitrary arguments and keyword arguments to be passed in.
    """

    def msg(self, *args, **kw):
        """
        Return tuple of ``args, kw`` or just ``args[0]`` if only one arg passed
        """
        # Slightly convoluted for backwards compatibility.
        if len(args) == 1 and not kw:
            return args[0]
        else:
            return args, kw

    log = debug = info = warn = warning = msg
    fatal = failure = err = error = critical = exception = msg
