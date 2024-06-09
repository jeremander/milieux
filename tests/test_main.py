from datetime import datetime
import json
from pathlib import Path
import subprocess
from typing import get_args, get_type_hints

from milieux import PROG
from milieux.cli.main import MilieuxCLI
from milieux.config import Config, user_default_base_dir, user_default_config_path
from milieux.distro import Distro
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

def check_package(env: Environment, pkg_name: str, exists: bool, editable: bool = False) -> None:
    glob = env.site_packages_path.glob(f'{pkg_name}*.dist-info' if editable else pkg_name)
    pkg_dirs = [p for p in glob if p.is_dir()]
    if exists:
        assert len(pkg_dirs) == 1
        if not editable:
            init_py = pkg_dirs[0] / '__init__.py'
            assert init_py.exists()
    else:
        assert not pkg_dirs

def get_module_path(env: Environment, pkg_name: str) -> str:
    python_exec = env.bin_path / 'python'
    cmd = [str(python_exec), '-c', f'import {pkg_name}; print({pkg_name}.__file__)']
    return subprocess.check_output(cmd, text=True)


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
        # test default config path
        check_main(['config', 'path'], stdout=str(cfg_path))
        # override config path with nonexistent path
        p = Path(tmp_config.base_dir) / 'test.toml'
        check_main(['-c', str(p), 'config', 'path'], stderr=f'Could not find config file {p}', success=False)
        # override config path with valid path
        p.touch()
        check_main(['-c', str(p), 'config', 'path'], stdout=str(p))
        # empty config file uses default values
        cfg = Config.from_toml_string(subprocess.check_output([PROG, '-c', str(p), 'config', 'show'], text=True))
        assert cfg.env_dir == Config().env_dir
        # override config path with existent path with invalid extension
        p = Path(tmp_config.base_dir) / 'test'
        p.touch()
        check_main(['-c', str(p), 'config', 'path'], stderr=f'Invalid config file {p}', success=False)


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
            return Path(tmp_config.distro_dir_path / f'{name}.txt')
        name = 'mydist'
        # list all distros
        check_main(['distro', 'list'], stdout='No distros exist')
        # show nonexistent distro
        check_main(['distro', 'show', name], stderr=f'No distro named {name!r}', success=False)
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
        req_path = projects_path / f'{name}.txt'
        req_path.write_text('pkg1\npkg3\n pkg2  \n')
        output = [f'Distro {name!r} already exists', f'Creating distro {name!r}', f'Wrote {name!r} requirements to']
        check_main(['distro', 'new', name, '-r', str(req_path), '-f'], stderr=output)
        self._check_distro(distro_path, ['pkg1', 'pkg2', 'pkg3'])
        # create distro with both packages and requirements file
        check_main(['distro', 'new', name, '--packages', 'pkg4', '-r', str(req_path), '-f'], stderr=output)
        self._check_distro(distro_path, ['pkg1', 'pkg2', 'pkg3', 'pkg4'])
        # create distro from another one
        check_main(['distro', 'new', 'mydist_copy', '-d', name], stderr="Wrote 'mydist_copy' requirements to")
        self._check_distro(get_distro_path('mydist_copy'), ['pkg1', 'pkg2', 'pkg3', 'pkg4'])
        # use nonexistent requirements file
        check_main(['distro', 'new', name, '-r', 'fake_reqs.txt', '-f'], stderr='No requirements file: fake_reqs.txt', success=False)
        # remove distro
        check_main(['distro', 'remove', 'mydist'], stderr="Deleting 'mydist' distro")
        check_main(['distro', 'remove', 'mydist_copy'], stderr="Deleting 'mydist_copy' distro")
        check_main(['distro', 'list'], stdout='No distros exist')
        # remove nonexistent distro
        check_main(['distro', 'remove', 'mydist'], stderr="No distro named 'mydist'", success=False)

    def test_lock(self, monkeypatch, tmp_config):
        projects_path = tmp_config.base_dir_path / 'projects'
        projects_path.mkdir()
        monkeypatch.chdir(projects_path)
        check_main(['scaffold', 'project1'])
        name = 'mydist'
        # stdlib package not valid
        check_main(['distro', 'new', name, '--packages', 'os'], stderr=f'Wrote {name!r} requirements')
        distro = Distro(name)
        self._check_distro(distro.path, ['os'])
        output = ['No solution found', 'os was not found in the package registry']
        check_main(['distro', 'lock', name], stderr=output, success=False)
        # use local package
        check_main(['distro', 'new', name, '--packages', 'file://project1', '-f'], stderr=f'Wrote {name!r} requirements')
        output = ['This file was autogenerated', 'project1']
        check_main(['distro', 'lock', name], stderr=f'Locking dependencies for {name!r} distro', stdout=output)
        self._check_distro(distro.path, ['file://project1'])
        # save a new distro (uses a date suffix)
        check_main(['distro', 'lock', name, '--new'], stderr=r"Wrote 'mydist.\d{8}' requirements to")
        # attempt to save distro to an existing one
        check_main(['distro', 'lock', name, '--new', name], stderr=f'Distro {name!r} already exists', success=False)
        # use nonexistent local package
        check_main(['distro', 'new', name, '--packages', 'file://project2', '-f'], stderr=f'Wrote {name!r} requirements')
        check_main(['distro', 'lock', name], stderr='No such file or directory', success=False)


class TestEnv:

    def test_env(self, tmp_config):
        assert not tmp_config.env_dir_path.exists()
        # list all environments
        check_main(['env', 'list'], stdout='No environments exist')
        # show nonexistent environment
        check_main(['env', 'show', 'myenv'], stderr="No environment named 'myenv'", success=False)
        # create environment
        env_dir = tmp_config.env_dir_path / 'myenv'
        out = [f"Creating environment 'myenv' in {env_dir}", f'{PROG} env activate myenv']
        check_main(['env', 'new'], stdin=['myenv'], stderr=out)
        assert env_dir.exists()
        for subdir in ['bin', 'lib']:
            assert (env_dir / subdir).exists()
        # try to create already-existing environment
        check_main(['env', 'new', 'myenv'], stderr="Environment 'myenv' already exists", success=False)
        # try to create environment with invalid Python executable
        check_main(['env', 'new', 'fake_env', '--python', 'fake-python'], stderr='executable `fake-python` not found', success=False)
        # list all environments
        check_main(['env', 'list'], stdout=['Environments:', r'\s+myenv'])
        # show single environment
        d = {'name': 'myenv', 'path': str(env_dir), 'created_at': datetime.fromtimestamp(env_dir.stat().st_ctime).isoformat()}
        check_main(['env', 'show', 'myenv'], stdout=json.dumps(d, indent=2))
        # show nonexistent environment
        check_main(['env', 'show', 'fake_env'], stderr="No environment named 'fake_env'", success=False)
        # activate nonexistent environment
        check_main(['env', 'activate', 'fake_env'], stderr="No environment named 'fake_env'", success=False)
        # activate environment (doesn't really activate, just prints the command)
        check_main(['env', 'activate', 'myenv'], stderr='To activate the environment.+/workspace/envs/myenv/bin/activate')
        # remove environment
        check_main(['env', 'remove', 'myenv'], stderr="Deleting 'myenv' environment")
        check_main(['env', 'list'], stdout='No environments exist')
        # remove nonexistent environment
        check_main(['env', 'remove', 'myenv'], stderr="No environment named 'myenv'", success=False)

    def test_install(self, monkeypatch, tmp_config):
        check_main(['env', 'new'], stdin=['myenv'])
        # create two local packages, for test installations
        projects_path = tmp_config.base_dir_path / 'projects'
        projects_path.mkdir()
        monkeypatch.chdir(projects_path)
        check_main(['scaffold', 'project1'])
        check_main(['scaffold', 'project2'])
        # attempt to install nothing
        check_main(['env', 'install', 'myenv'], stderr='Must specify packages to install', success=False)
        # attempt to install into nonexistent environment
        check_main(['env', 'install', 'fake_env', '-p', 'file://project1'], stderr="No environment named 'fake_env'", success=False)
        # install package into environment
        check_main(['env', 'install', 'myenv', '-p', 'file://project1'], stderr=["Installing dependencies into 'myenv' environment", 'file://project1'])
        name = 'myenv'
        env = Environment(name)
        check_package(env, 'project1', True)
        check_package(env, 'project2', False)
        # check module path is within environment (regular file install)
        module_path = get_module_path(env, 'project1')
        assert module_path.startswith(str(env.dir_path))
        assert not module_path.startswith(str(projects_path.resolve()))
        # install requirements file into environment
        reqs_path = projects_path / 'reqs.txt'
        with open(reqs_path, 'w') as f:
            print('file://project2', file=f)
        check_main(['env', 'install', name, '-r', str(reqs_path)], stderr=f'-r {reqs_path}')
        check_package(env, 'project1', True)
        check_package(env, 'project2', True)
        # print out packages in environment
        check_main(['env', 'freeze', name], stdout='project1 @ file:///.+project2 @ file:///')
        check_main(['env', 'show', name, '--list-packages'], stdout=r'"name": "myenv".+"packages": \[\s*"project1 @ file:///')
        # test editable install (overwrite projects)
        # install a single editable package directly
        check_main(['env', 'install', name, '-e', 'project1'])
        check_package(env, 'project1', True, editable=True)
        check_package(env, 'project2', True)
        module_path = get_module_path(env, 'project1')
        assert module_path.startswith(str((projects_path / 'project1').resolve()))
        assert not module_path.startswith(str(env.dir_path))
        # use -e flag within a requirements file
        with open(reqs_path, 'w') as f:
            print('-e file://project2', file=f)
        check_main(['env', 'install', name, '-r', str(reqs_path)])
        check_package(env, 'project1', True, editable=True)
        check_package(env, 'project2', True, editable=True)
        # uninstall package
        check_main(['env', 'uninstall', name, '-p', 'project1'], stderr=["Uninstalling dependencies from 'myenv' environment", 'project1'])
        check_package(env, 'project1', False)
        check_package(env, 'project2', True, editable=True)
        check_main(['env', 'uninstall', name, '-r', str(reqs_path)], stderr=f'-r {reqs_path}')
        check_package(env, 'project1', False)
        check_package(env, 'project2', False)
        # uninstall nonexistent package
        check_main(['env', 'uninstall', name, '-p', 'project3'], stderr='project3', success=False)

    def test_sync(self, monkeypatch, tmp_config):
        # create two local packages, for test installations
        projects_path = tmp_config.base_dir_path / 'projects'
        projects_path.mkdir()
        monkeypatch.chdir(projects_path)
        check_main(['scaffold', 'project1'])
        check_main(['scaffold', 'project2'])
        check_main(['distro', 'new', 'mydist', '-p', 'file://project1'])
        check_main(['env', 'new', 'myenv'])
        # sync distro into environment
        check_main(['env', 'sync', 'myenv', '-d', 'mydist'], stderr="Syncing dependencies in 'myenv' environment")
        env = Environment('myenv')
        check_package(env, 'project1', True)
        check_package(env, 'project2', False)
        # install another dependency
        check_main(['env', 'install', 'myenv', '-p', 'file://project2'])
        check_package(env, 'project1', True)
        check_package(env, 'project2', True)
        # sync distro again (removes the newly installed package)
        check_main(['env', 'sync', 'myenv', '-d', 'mydist'])
        check_package(env, 'project1', True)
        check_package(env, 'project2', False)
        # sync nonexistent distro
        check_main(['env', 'sync', 'myenv', '-d', 'fake_dist'], stderr="No distro named 'fake_dist'", success=False)
