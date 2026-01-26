from pathlib import Path
import os

_ENV_ROOT = os.getenv('LW_PROJECT_ROOT')

def _find_project_root(start_path: Path) -> Path:
    cur = start_path.resolve()
    # Walk up until we find manage.py or requirements.txt or .git
    root_indicators = {'manage.py', 'requirements.txt', '.git'}
    while True:
        if any((cur / name).exists() for name in root_indicators):
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    raise RuntimeError('Could not locate project root (manage.py or requirements.txt). Set LW_PROJECT_ROOT to override.')


def get_project_root() -> Path:
    if _ENV_ROOT:
        p = Path(_ENV_ROOT)
        if p.exists():
            return p.resolve()
        raise RuntimeError(f'LW_PROJECT_ROOT is set but path does not exist: {_ENV_ROOT}')
    # start from this file's location
    start = Path(__file__).resolve().parent.parent
    return _find_project_root(start)


PROJECT_ROOT = get_project_root()
CONFIG_DIR = Path(os.getenv('LW_CONFIG_DIR', PROJECT_ROOT / 'config'))
SQL_DIR = Path(os.getenv('LW_SQL_DIR', PROJECT_ROOT / 'sql'))
SCRIPTS_DIR = Path(os.getenv('LW_SCRIPTS_DIR', PROJECT_ROOT / 'scripts'))
TEMPLATES_DIR = Path(os.getenv('LW_TEMPLATES_DIR', PROJECT_ROOT / 'templates'))
STATIC_DIR = Path(os.getenv('LW_STATIC_DIR', PROJECT_ROOT / 'static'))
DATA_DIR = Path(os.getenv('LW_DATA_DIR', PROJECT_ROOT / 'data'))

def ensure_dirs_exist():
    missing = []
    for name, d in (('config', CONFIG_DIR), ('sql', SQL_DIR), ('scripts', SCRIPTS_DIR)):
        if not d.exists():
            missing.append(str(d))
    if missing:
        raise RuntimeError('Missing required project directories: ' + ', '.join(missing))
