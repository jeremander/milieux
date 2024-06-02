from contextlib import contextmanager
import sys
from typing import get_args, get_type_hints

import pytest

from milieux.cli.main import MilieuxCLI


@contextmanager
def cli_args(*argv):
    """Temporarily sets the arguments in sys.argv."""
    sys_argv = sys.argv
    try:
        sys.argv = [sys.executable] + list(argv)
        yield
    finally:
        sys.argv = sys_argv

def test_main_missing_args(capsys):
    """Tests running the main program with no arguments."""
    with cli_args():
        with pytest.raises(SystemExit) as e:  # noqa: PT012
            MilieuxCLI.main()
            assert e.code == 1
        assert 'error: the following arguments are required: subcommand' in capsys.readouterr().err

def test_main_help(capsys):
    """Tests running the main program with --help."""
    with cli_args('--help'):
        with pytest.raises(SystemExit) as e:  # noqa: PT012
            MilieuxCLI.main()
            assert e.code == 0
        assert '--help' in capsys.readouterr().out

def test_subcommand_help(capsys):
    """Tests running each of the subcommands with --help."""
    for subcmd in get_args(get_type_hints(MilieuxCLI)['subcommand']):
        cmd_name = subcmd.__settings__.command_name
        with cli_args(cmd_name, '--help'):
            with pytest.raises(SystemExit) as e:  # noqa: PT012
                MilieuxCLI.main()
                assert e.code == 0
        msg = capsys.readouterr().out
        assert cmd_name in msg
        assert '--help' in msg
