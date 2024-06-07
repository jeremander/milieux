from datetime import datetime
import json
from typing import get_args, get_type_hints

from milieux import PROG
from milieux.cli.main import MilieuxCLI
from milieux.config import Config, user_default_base_dir, user_default_config_path

from . import check_main


def test_main_missing_args():
    """Tests running the main program with no arguments."""
    check_main([], stderr='error: the following arguments are required: subcommand', success=False)

def test_main_help():
    """Tests running the main program with --help."""
    check_main(['--help'], stdout='--help')

def test_subcommand_help():
    """Tests running each of the subcommands with --help."""
    for subcmd in get_args(get_type_hints(MilieuxCLI)['subcommand']):
        cmd_name = subcmd.__settings__.command_name
        check_main([cmd_name, '--help'], stdout=[cmd_name, '--help'])


##########
# CONFIG #
##########

class TestConfig:

    def test_config_show_no_config(self, tmp_config):
        user_default_config_path().unlink()  # delete config file
        check_main(['config', 'show'], stderr='No config file found', success=False)

    def test_config_new(self, tmp_config):
        cfg_path = user_default_config_path()
        user_default_config_path().unlink()  # delete config file
        base_dir = user_default_base_dir()
        assert base_dir.exists()
        check_main(['config', 'new'], stdin=['', '', ''], stderr=f'Saved config file to {cfg_path}')
        cfg = Config.load_config(cfg_path)
        assert cfg.base_dir == str(base_dir)
        out = f'base_dir = "{base_dir}"'
        assert cfg.env_dir_path == Config().env_dir_path
        check_main(['config', 'show'], stdout=out)
        # attempt to create another config file but say no to overwriting
        check_main(['config', 'new'], stdin=['no'], stdout='already exists')
        # overwrite config file
        check_main(['config', 'new'], stdin=['yes', '', 'envs2', ''], stderr=f'Saved config file to {cfg_path}')
        cfg = Config.load_config(cfg_path)
        assert cfg.base_dir == str(base_dir)
        assert cfg.env_dir_path == Config().env_dir_path.with_name('envs2')

    def test_config_path(self, tmp_config):
        cfg_path = user_default_config_path()
        check_main(['config', 'path'], stdout=str(cfg_path))


class TestEnv:

    def test_env(self, tmp_config):
        # show all environments
        check_main(['env', 'show'], stdout='No environments exist')
        # show nonexistent environment
        check_main(['env', 'show', '-n', 'myenv'], stderr="No environment named 'myenv'", success=False)
        # create environment
        env_dir = tmp_config.env_dir_path / 'myenv'
        out = [f"Creating environment 'myenv' in {env_dir}", f'{PROG} env activate myenv']
        check_main(['env', 'create'], stdin=['myenv'], stderr=out)
        assert env_dir.exists()
        for subdir in ['bin', 'lib']:
            assert (env_dir / subdir).exists()
        # try to create already-existing environment
        check_main(['env', 'create', '-n', 'myenv'], stderr="Environment 'myenv' already exists", success=False)
        # try to create environment with invalid Python executable
        check_main(['env', 'create', '-n', 'myenv2', '--python', 'fake-python'], stderr='executable `fake-python` not found', success=False)
        # show all environments
        check_main(['env', 'show'], stdout=r'Environments:\s+myenv')
        # show single environment
        d = {'name': 'myenv', 'path': str(env_dir), 'created_at': datetime.fromtimestamp(env_dir.stat().st_ctime).isoformat()}
        check_main(['env', 'show', '-n', 'myenv'], stdout=json.dumps(d, indent=2))
        # TODO: install, activate
        # remove environment
        check_main(['env', 'remove', '-n', 'myenv'], stderr="Deleting 'myenv' environment")
        check_main(['env', 'show'], stdout='No environments exist')
        # remove nonexistent environment
        check_main(['env', 'remove', '-n', 'myenv'], stderr="No environment named 'myenv'", success=False)


class TestScaffold:

    def test_scaffold(self, monkeypatch, tmp_config):
        # set up a new project
        projects_path = tmp_config.base_dir_path / 'projects'
        projects_path.mkdir()
        monkeypatch.chdir(projects_path)
        check_main(['scaffold', 'my_project'], stderr="Creating new project 'my_project' with 'hatch' utility")
        project_path = projects_path / 'my_project'
        assert project_path.is_dir()
        assert (project_path / 'README.md').exists()
