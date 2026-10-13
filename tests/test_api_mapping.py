"""API crosswalk and audit-signature regression tests."""
import pytest
from fastapi.testclient import TestClient
from agents.api import app
from agents.base import AuditTrail

client = TestClient(app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_api_reference_table():
    response = client.get("/api/mapping")
    assert response.status_code == 200
    assert len(response.json()["crosswalk"]) == 6
    assert response.json()["crosswalk"][4]["kps_values"] == [10,20]


@pytest.mark.parametrize("payload,result", [
    ({"ecog": 1}, {"ecog": 1, "kps_values": [70,80]}),
    ({"kps": 0}, {"ecog": 5, "kps_values": [0]}),
    ({"kps": 100}, {"ecog": 0, "kps_values": [90,100]}),
])
def test_api_maps(payload,result):
    response = client.post("/api/map",json=payload)
    assert response.status_code == 200
    for key,value in result.items():
        assert response.json()[key] == value


@pytest.mark.parametrize("payload", [
    {}, {"ecog": 2, "kps": 50}, {"ecog": -1}, {"ecog": 6},
    {"kps": 55}, {"kps": 110}, {"kps": -10}, {"ecog": 2.3},
    {"kps": "NaN"}
])
def test_api_rejects_invalid(payload):
    assert client.post("/api/map",json=payload).status_code == 422


def test_static_app_is_served():
    response=client.get("/")
    assert response.status_code==200
    assert "ECOG–Karnofsky Mapper" in response.text
    assert "GROUPS = [[90,100],[70,80],[50,60],[30,40],[10,20],[0]]" in response.text
    assert 'fetch("/api/audit")' not in response.text


def test_audit_integrity_rejects_modified_signature():
    trail=AuditTrail(secret_key="test-only-in-memory-key")
    trail.log("tester","test","event",{"status":"ok"})
    assert trail.verify_integrity()
    trail.logs[0]["actor"]="forged"
    assert not trail.verify_integrity()


def test_audit_integrity_checks_all_blocks_and_snapshots():
    trail=AuditTrail(secret_key="test-only-in-memory-key")
    trail.log("tester","test","one",{})
    trail.log("tester","test","two",{})
    assert trail.verify_integrity()
    snapshot=trail.get_trail()
    snapshot[0]["current_hash"]="forged"
    assert trail.verify_integrity()
    trail.logs[0]["payload_hash"]="forged"
    assert not trail.verify_integrity()
