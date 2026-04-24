from pathlib import Path


def test_config_path_exists():
    assert Path("etl/config/settings.yaml").exists()


def test_entrypoint_exists():
    assert Path("etl.py").exists()
