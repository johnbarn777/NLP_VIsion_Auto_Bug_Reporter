from pathlib import Path

import yaml


def test_compose_has_api_worker_and_data_volume():
    data = yaml.safe_load(Path("compose.yaml").read_text())
    services = data.get("services", {})
    assert "api" in services and "worker" in services
    for name in ("api", "worker"):
        vols = services[name].get("volumes", [])
        assert "./data:/data" in vols
