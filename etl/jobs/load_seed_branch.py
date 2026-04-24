from pathlib import Path


def ensure_branch_seed_exists() -> Path:
    path = Path("data/seed/branches.csv")
    if not path.exists():
        raise FileNotFoundError("Missing seed file: data/seed/branches.csv")
    return path
