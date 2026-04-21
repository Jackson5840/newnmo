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
