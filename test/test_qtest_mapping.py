"""Unit tests for the qTest requirement → DB-field mapping.

Pure/infra-free: no Postgres, Neo4j, qTest, or LLM needed. Guards the ingestion
gap where the real requirement content lives in the qTest item's ``properties[]``
array (Description/Status/Priority/Release) rather than at the top level, so a
top-level-only pull produces empty-bodied requirement shells.
"""
from database.qtest_db import map_qtest_requirement


def _item(name="A requirement", properties=None):
    return {"id": 1, "name": name, "properties": properties or []}


def test_extracts_description_from_properties_with_html_stripped():
    item = _item(properties=[
        {"field_name": "Description",
         "field_value": "<p>Match caseworker language skills with client preference.</p>"},
    ])
    mapped = map_qtest_requirement(item)
    assert mapped["description"] == "Match caseworker language skills with client preference."


def test_extracts_status_priority_and_sprint_from_release():
    item = _item(properties=[
        {"field_name": "Status", "field_value_name": "Approved"},
        {"field_name": "Priority", "field_value_name": "Medium"},
        {"field_name": "Release", "field_value_name": "Sprint 3"},
    ])
    mapped = map_qtest_requirement(item)
    assert mapped["status"] == "Approved"
    assert mapped["priority"] == "Medium"
    assert mapped["sprint"] == "Sprint 3"


def test_title_comes_from_name():
    assert map_qtest_requirement(_item(name="Reset a password"))["title"] == "Reset a password"


def test_missing_name_falls_back_to_untitled():
    assert map_qtest_requirement({"id": 2})["title"] == "Untitled"


def test_no_properties_yields_safe_defaults():
    mapped = map_qtest_requirement(_item(properties=[]))
    assert mapped["description"] == ""
    assert mapped["status"] == "New"
    assert mapped["priority"] == ""
    assert mapped["sprint"] == ""


def test_field_name_match_is_case_insensitive():
    item = _item(properties=[{"field_name": "description", "field_value": "plain text"}])
    assert map_qtest_requirement(item)["description"] == "plain text"


def test_unknown_properties_are_ignored():
    item = _item(properties=[{"field_name": "Type", "field_value_name": "Functional"}])
    mapped = map_qtest_requirement(item)
    assert "Functional" not in mapped.values()
