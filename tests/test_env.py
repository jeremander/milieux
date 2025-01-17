import os
import sys

from milieux.env import Environment, get_active_environment, get_env_base_dir


def test_get_active_environment(monkeypatch, tmp_config):
    base_dir = get_env_base_dir()
    assert get_active_environment() is None
    monkeypatch.setitem(os.environ, 'VIRTUAL_ENV', '')
    assert get_active_environment() is None
    monkeypatch.setitem(os.environ, 'VIRTUAL_ENV', 'myenv')
    assert get_active_environment() is None
    monkeypatch.setitem(os.environ, 'VIRTUAL_ENV', str(base_dir / 'myenv'))
    assert get_active_environment() == Environment('myenv', base_dir)


def test_template(monkeypatch, tmp_config):
    name = 'myenv'
    env = Environment(name)
    pyversion = sys.version.split()[0]
    pyversion_minor = '.'.join(pyversion.split('.')[:2])
    monkeypatch.setattr('milieux.env.Environment.env_dir', env.dir_path / name)
    monkeypatch.setattr('milieux.env.Environment.python_version', pyversion)
    env_vars = env.template_env_vars
    assert env_vars['ENV_NAME'] == name
    assert env_vars['ENV_BASE_DIR'] == tmp_config.env_dir_path
    assert env_vars['ENV_DIR'] == tmp_config.env_dir_path / name
    assert env_vars['ENV_PYVERSION'] == pyversion
    assert env_vars['ENV_PYVERSION_MINOR'] == pyversion_minor
    assert env_vars['ENV_SITE_PACKAGES_DIR'] == tmp_config.env_dir_path / name / 'lib' / f'python{pyversion_minor}' / 'site-packages'
