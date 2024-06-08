from datetime import datetime
import json
from pathlib import Path
from typing import get_args, get_type_hints

from milieux import PROG
from milieux.cli.main import MilieuxCLI
from milieux.config import Config, user_default_base_dir, user_default_config_path
from milieux.env import Environment
from milieux.utils import read_lines

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


class TestDistro:

    def _check_distro(self, distro_path, packages):
        name = distro_path.stem
        lines = read_lines(distro_path)
        assert lines == packages
        # check that 'show' command prints out the packages
        check_main(['distro', 'show', name], stderr=f'Distro {name!r} is located at: {distro_path}', stdout=packages)

    def test_distro(self, monkeypatch, tmp_config):
        projects_path = tmp_config.base_dir_path / 'projects'
        projects_path.mkdir()
        monkeypatch.chdir(projects_path)
        assert not tmp_config.distro_dir_path.exists()
        def get_distro_path(name: str) -> Path:
            return Path(tmp_config.distro_dir_path / f'{name}.in')
        name = 'mydist'
        # list all distros
        check_main(['distro', 'list'], stdout='No distros exist')
        # show nonexistent distro
        check_main(['distro', 'show', name], stderr=f'No distribution named {name!r}', success=False)
        # create distro with no packages
        check_main(['distro', 'new', name], stderr='Must specify at least one package', success=False)
        assert not get_distro_path(name).exists()
        # create distro with packages
        check_main(['distro', 'new', name, '--packages', 'pkg1', 'pkg2'], stderr=f'Wrote {name!r} requirements to')
        distro_path = get_distro_path(name)
        assert distro_path.exists()
        self._check_distro(distro_path, ['pkg1', 'pkg2'])
        # list all distros
        check_main(['distro', 'list'], stdout=['Distros:', r'\s+mydist'])
        # write same distro without -f flag
        check_main(['distro', 'new', name, '--packages', 'pkg1'], stderr=f'Distro {name!r} already exists', success=False)
        # create distro with requirements file
        req_path = projects_path / f'{name}.in'
        req_path.write_text('pkg1\npkg3\n pkg2  \n')
        output = [f'Distro {name!r} already exists', f'Wrote {name!r} requirements to']
        check_main(['distro', 'new', name, '-r', str(req_path), '-f'], stderr=output)
        self._check_distro(distro_path, ['pkg1', 'pkg2', 'pkg3'])
        # create distro with both packages and requirements file
        check_main(['distro', 'new', name, '--packages', 'pkg4', '-r', str(req_path), '-f'], stderr=output)
        self._check_distro(distro_path, ['pkg1', 'pkg2', 'pkg3', 'pkg4'])
        # use nonexistent requirements file
        check_main(['distro', 'new', name, '-r', 'fake_reqs.in', '-f'], stderr='No requirements file: fake_reqs.in', success=False)


    def test_env(self, tmp_config):
        assert not tmp_config.env_dir_path.exists()
        # list all environments
        check_main(['env', 'list'], stdout='No environments exist')
        # show nonexistent environment
        check_main(['env', 'show', '-n', 'myenv'], stderr="No environment named 'myenv'", success=False)
        # create environment
        env_dir = tmp_config.env_dir_path / 'myenv'
        out = [f"Creating environment 'myenv' in {env_dir}", f'{PROG} env activate myenv']
        check_main(['env', 'new'], stdin=['myenv'], stderr=out)
        assert env_dir.exists()
        for subdir in ['bin', 'lib']:
            assert (env_dir / subdir).exists()
        # try to create already-existing environment
        check_main(['env', 'new', '-n', 'myenv'], stderr="Environment 'myenv' already exists", success=False)
        # try to create environment with invalid Python executable
        check_main(['env', 'new', '-n', 'fake_env', '--python', 'fake-python'], stderr='executable `fake-python` not found', success=False)
        # list all environments
        check_main(['env', 'list'], stdout=['Environments:', r'\s+myenv'])
        # show single environment
        d = {'name': 'myenv', 'path': str(env_dir), 'created_at': datetime.fromtimestamp(env_dir.stat().st_ctime).isoformat()}
        check_main(['env', 'show', '-n', 'myenv'], stdout=json.dumps(d, indent=2))
        # show nonexistent environment
        check_main(['env', 'show', '-n', 'fake_env'], stderr="No environment named 'fake_env'", success=False)
        # activate nonexistent environment
        check_main(['env', 'activate', '-n', 'fake_env'], stderr="No environment named 'fake_env'", success=False)
        # activate environment (doesn't really activate, just prints the command)
        check_main(['env', 'activate', '-n', 'myenv'], stderr='To activate the environment.+/workspace/envs/myenv/bin/activate')
        # remove environment
        check_main(['env', 'remove', '-n', 'myenv'], stderr="Deleting 'myenv' environment")
        check_main(['env', 'list'], stdout='No environments exist')
        # remove nonexistent environment
        check_main(['env', 'remove', '-n', 'myenv'], stderr="No environment named 'myenv'", success=False)

    def test_install(self, monkeypatch, tmp_config):
        check_main(['env', 'new'], stdin=['myenv'])
        # create two local packages, for test installations
        projects_path = tmp_config.base_dir_path / 'projects'
        projects_path.mkdir()
        monkeypatch.chdir(projects_path)
        check_main(['scaffold', 'project1'])
        check_main(['scaffold', 'project2'])
        # attempt to install nothing
        check_main(['env', 'install', '-n', 'myenv'], stderr='Must specify packages to install', success=False)
        # attempt to install into nonexistent environment
        check_main(['env', 'install', '-n', 'fake_env', 'file://project1'], stderr="No environment named 'fake_env'", success=False)
        # install package into environment
        check_main(['env', 'install', '-n', 'myenv', 'file://project1'], stderr='file://project1')
        env = Environment('myenv')
        def check_pkg(pkg_name: str, exists: bool) -> None:
            pkg_dir = env.site_packages_path / pkg_name
            if exists:
                assert pkg_dir.exists()
                init_py = pkg_dir / '__init__.py'
                assert init_py.exists()
            else:
                assert not pkg_dir.exists()
        check_pkg('project1', True)
        check_pkg('project2', False)
        # install requirements file into environment
        reqs_path = projects_path / 'reqs.txt'
        with open(reqs_path, 'w') as f:
            print('file://project2', file=f)
        check_main(['env', 'install', '-n', 'myenv', '-r', str(reqs_path)], stderr=f'-r {reqs_path}')
        check_pkg('project1', True)
        check_pkg('project2', True)
        # print out packages in environment
        check_main(['env', 'freeze', '-n', 'myenv'], stdout='project1 @ file:///.+project2 @ file:///')
        check_main(['env', 'show', '-n', 'myenv', '--list-packages'], stdout=r'"name": "myenv".+"packages": \[\s*"project1 @ file:///')
        # uninstall package
        check_main(['env', 'uninstall', '-n', 'myenv', 'project1'], stderr='project1')
        check_pkg('project1', False)
        check_pkg('project2', True)
        check_main(['env', 'uninstall', '-n', 'myenv', '-r', str(reqs_path)], stderr=f'-r {reqs_path}')
        check_pkg('project1', False)
        check_pkg('project2', False)
        # uninstall nonexistent package
        check_main(['env', 'uninstall', '-n', 'myenv', 'project3'], stderr='project3', success=False)


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
