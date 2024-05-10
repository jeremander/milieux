from pathlib import Path


# def run_command(cmd: list[Any], **kwargs: Any) -> subprocess.CompletedProcess:
#     """Runs a command (provided as a list) via subprocess."""

def resolve_path(path: str, base_dir: Path) -> Path:
    """Attempts to resolve a path to an absolute path.
    If it is a relative path, resolves it relative to the given base_dir."""
    p = Path(path)
    first_part = p.parts[0] if p.parts else None
    if p.is_absolute() or (first_part == '.'):
        if p.exists():
            return p
        raise FileNotFoundError(path)
    if first_part == '..':
        return resolve_path(str(p.resolve()), base_dir)
    # otherwise, a relative path
    return base_dir / path
