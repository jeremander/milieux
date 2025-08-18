from contextlib import contextmanager, nullcontext, redirect_stderr, redirect_stdout
from io import StringIO
import logging
from pathlib import Path
import re
import sys
from typing import Annotated, Optional, Union
from unittest.mock import patch

from typing_extensions import Doc

from milieux import logger
from milieux.cli.main import MilieuxCLI


Args = Union[str, list[str]]

# test data directory
TEST_DATA_DIR = Path(__file__).with_name('data')


@contextmanager
def cli_args(*args):
    """Temporarily sets the arguments in sys.argv."""
    sys_argv = sys.argv
    try:
        sys.argv = [sys.executable] + list(args)
        yield
    finally:
        sys.argv = sys_argv

@contextmanager
def patch_stdin(content):
    """Patches stdin with the given input."""
    with patch('sys.stdin', StringIO(content)):
        yield


def set_logger_stream(stream):
    """Sets the root logger stream to the given stream."""
    for handler in logger.parent.handlers:  # type: ignore[union-attr]
        if isinstance(handler, logging.StreamHandler):
            handler.stream = stream


def check_main(
    args: Annotated[list[str], Doc('list of arguments to main program')],
    stdin: Annotated[Optional[Args], Doc('user inputs for interactive prompts')] = None,
    stdout: Annotated[Optional[Args], Doc('expected stdout (regular expression)')] = None,
    stderr: Annotated[Optional[Args], Doc('expected stderr (regular expression)')] = None,
    success: Annotated[bool, Doc('whether we expect success')] = True,
) -> None:
    """Generic test harness for running the main CLI program."""
    if isinstance(stdin, str):
        stdin = [stdin]
    if isinstance(stdout, str):
        stdout = [stdout]
    if isinstance(stderr, str):
        stderr = [stderr]
    stdin_context = patch_stdin(''.join(line + '\n' for line in stdin)) if stdin else nullcontext()
    stdout_ctx = nullcontext() if (stdout is None) else redirect_stdout(StringIO())
    stderr_ctx = nullcontext() if (stderr is None) else redirect_stderr(StringIO())
    with cli_args(*args), stdin_context, stdout_ctx as sio_out, stderr_ctx as sio_err:
        # capture logger output
        if sio_err:
            set_logger_stream(sio_err)
        try:
            MilieuxCLI.main()
        except SystemExit as e:
            assert success == (e.code == 0)  # noqa: PT017
        except Exception:
            assert not success
        else:
            assert success
        finally:
            if sio_err:
                set_logger_stream(sys.stderr)
        flags = re.MULTILINE | re.DOTALL  # novermin
        if stdout is not None:
            assert sio_out is not None
            for s in stdout:
                assert re.search(s, sio_out.getvalue(), flags=flags)
        if stderr is not None:
            assert sio_err is not None
            for s in stderr:
                assert re.search(s, sio_err.getvalue(), flags=flags)
