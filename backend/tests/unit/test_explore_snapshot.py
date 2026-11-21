import json
from pathlib import Path

import pytest

from integrations.globalgiving import explore_snapshot
from integrations.globalgiving.explore_snapshot import ExploreSnapshot
from projects.models import (
    Continuation,
    DiscoveryResult,
    OrganizationReference,
    ProjectSummary,
)


@pytest.mark.parametrize("refresh", [0, 59, 1800])
def test_invalid_snapshot_interval(tmp_path, refresh):
    with pytest.raises(ValueError):
        ExploreSnapshot(tmp_path / "explore.json", refresh)


async def test_snapshot_atomic_file_preserves_previous_data(tmp_path, monkeypatch):
    path = tmp_path / "explore.json"
    snapshot = ExploreSnapshot(path, 600)
    initial = DiscoveryResult(
        (
            ProjectSummary(
                "1",
                organization=OrganizationReference("8", "Org", "https://org.example"),
            ),
        )
    )
    await snapshot.publish(initial)
    raw = path.read_bytes()
    assert json.loads(raw)["items"][0]["organization"] == {"id": "8", "name": "Org"}

    def interrupt(source: Path, target: Path):
        assert target == path and source != target and source.parent == target.parent
        assert source.exists()
        assert path.read_bytes() == raw
        raise OSError("test atomic replace failure")

    monkeypatch.setattr(explore_snapshot.os, "replace", interrupt)
    await snapshot.publish(DiscoveryResult((ProjectSummary("2"),)))
    assert path.read_bytes() == raw
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize(
    "invalid",
    [
        DiscoveryResult(),
        DiscoveryResult((ProjectSummary("1"), ProjectSummary("1"))),
        DiscoveryResult(
            (ProjectSummary("1", image_url="https://example.org/1.jpg?api_key=secret"),)
        ),
        DiscoveryResult(
            (
                ProjectSummary(
                    "1", image_url="https://example.org/1.jpg?signature=secret"
                ),
            )
        ),
        DiscoveryResult((ProjectSummary("1"),), Continuation("private")),
        DiscoveryResult((ProjectSummary("1", summary="x" * (128 * 1024)),)),
    ],
)
async def test_invalid_result_never_replaces_valid_file(tmp_path, invalid):
    path = tmp_path / "explore.json"
    snapshot = ExploreSnapshot(path, 600)
    await snapshot.publish(DiscoveryResult((ProjectSummary("2"),)))
    old = path.read_bytes()
    await snapshot.publish(invalid)
    assert path.read_bytes() == old
