"""Smoke tests for all API endpoints — verifies HTTP 200 responses."""

import requests

BASE_URL = "http://localhost:8002"


def get(path, **kwargs):
    return requests.get(f"{BASE_URL}{path}", **kwargs)


def test_root():
    r = get("/")
    assert r.status_code == 200


def test_quickstats():
    r = get("/quickstats/")
    assert r.status_code == 200


def test_clear():
    r = get("/clear")
    assert r.status_code == 200


def test_neuron_filter():
    r = get("/neuron/", params={"species_name": "rat"})
    assert r.status_code == 200


def test_neuron_random():
    r = get("/neuron/", params={"random": 2})
    assert r.status_code == 200


def test_neuron_count():
    r = get("/neuron/n/", params={"species_name": "rat"})
    assert r.status_code == 200


def test_browse():
    r = get("/browse/species/rat")
    assert r.status_code == 200


def test_chartcount():
    r = get("/chartcount/species_name/10")
    assert r.status_code == 200


def test_metacount_no_detail():
    r = get("/metacount/species_name", params={"detail": "false"})
    assert r.status_code == 200


def test_metacount_detail():
    r = get("/metacount/species_name", params={"detail": "true"})
    assert r.status_code == 200


def test_metavals():
    r = get("/metavals/", params={"fields": "species_name"})
    assert r.status_code == 200


def test_pvec():
    r = get("/pvec/test")
    assert r.status_code == 200


def test_measurements():
    r = get("/measurements/", params={"name": "test"})
    assert r.status_code == 200


def test_feedsearch():
    r = get("/feedsearch")
    assert r.status_code == 200


def test_search():
    r = get("/search/test")
    assert r.status_code == 200


# --- Cart endpoint tests ---

def test_cart_create():
    resp = requests.post(f"{BASE_URL}/cart/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "cart_token" in data
    assert data["count"] == 0


def test_cart_view_empty():
    resp = requests.post(f"{BASE_URL}/cart/")
    token = resp.json()["cart_token"]
    resp = get(f"/cart/{token}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 0
    assert data["names"] == []


def test_cart_not_found():
    resp = get("/cart/nonexistent-token")
    assert resp.status_code == 404


def test_cart_add_names():
    resp = requests.post(f"{BASE_URL}/cart/")
    token = resp.json()["cart_token"]
    resp = get("/neuron/", params={"random": 1})
    data = resp.json()["data"]
    if not data:
        return
    name = data[0]["name"]
    resp = requests.post(f"{BASE_URL}/cart/{token}/add", json={"names": [name]})
    assert resp.status_code == 200
    result = resp.json()
    assert result["count"] == 1
    resp = get(f"/cart/{token}")
    assert name in resp.json()["names"]


def test_cart_add_invalid_names():
    resp = requests.post(f"{BASE_URL}/cart/")
    token = resp.json()["cart_token"]
    resp = requests.post(f"{BASE_URL}/cart/{token}/add", json={"names": ["nonexistent_neuron_xyz"]})
    assert resp.status_code == 200
    result = resp.json()
    assert result["count"] == 0
    assert "nonexistent_neuron_xyz" in result["invalid_names"]


def test_cart_add_no_params():
    resp = requests.post(f"{BASE_URL}/cart/")
    token = resp.json()["cart_token"]
    resp = requests.post(f"{BASE_URL}/cart/{token}/add", json={})
    assert resp.status_code == 400


def test_cart_add_dedup():
    resp = requests.post(f"{BASE_URL}/cart/")
    token = resp.json()["cart_token"]
    resp = get("/neuron/", params={"random": 1})
    data = resp.json()["data"]
    if not data:
        return
    name = data[0]["name"]
    requests.post(f"{BASE_URL}/cart/{token}/add", json={"names": [name]})
    requests.post(f"{BASE_URL}/cart/{token}/add", json={"names": [name]})
    resp = get(f"/cart/{token}")
    assert resp.json()["count"] == 1


def test_cart_remove():
    resp = requests.post(f"{BASE_URL}/cart/")
    token = resp.json()["cart_token"]
    resp = get("/neuron/", params={"random": 2})
    data = resp.json()["data"]
    if len(data) < 2:
        return
    names = [d["name"] for d in data]
    requests.post(f"{BASE_URL}/cart/{token}/add", json={"names": names})
    resp = requests.post(f"{BASE_URL}/cart/{token}/remove", json={"names": [names[0]]})
    assert resp.status_code == 200
    assert resp.json()["count"] == 1


def test_cart_clear():
    resp = requests.post(f"{BASE_URL}/cart/")
    token = resp.json()["cart_token"]
    resp = get("/neuron/", params={"random": 1})
    data = resp.json()["data"]
    if not data:
        return
    requests.post(f"{BASE_URL}/cart/{token}/add", json={"names": [data[0]["name"]]})
    resp = requests.delete(f"{BASE_URL}/cart/{token}")
    assert resp.status_code == 200
    resp = get(f"/cart/{token}")
    assert resp.status_code == 404


def test_cart_download_empty():
    resp = requests.post(f"{BASE_URL}/cart/")
    token = resp.json()["cart_token"]
    resp = get(f"/cart/{token}/download")
    assert resp.status_code == 400


def test_cart_download():
    resp = requests.post(f"{BASE_URL}/cart/")
    token = resp.json()["cart_token"]
    resp = get("/neuron/", params={"random": 1})
    data = resp.json()["data"]
    if not data:
        return
    name = data[0]["name"]
    requests.post(f"{BASE_URL}/cart/{token}/add", json={"names": [name]})
    resp = get(f"/cart/{token}/download")
    assert resp.status_code == 200
    assert resp.headers.get("content-type") == "application/x-zip-compressed"
