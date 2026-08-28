""" "
Tests for app.py
"""

import re
from unittest.mock import Mock, patch

import pytest

from snowtask.app import Filter, SnowTask, TabbedContent, TaskTable
from snowtask.config import ConfigPreferences
from snowtask.database import Database


# Fixtures
@pytest.fixture
def valid_task_data():
    """
    Valid task data, as would be returned from Database's
    get_tasks method.
    """
    return [
        {
            "created_on": "2026-03-19",
            "name": "strip_metadata",
            "database_name": "PROD",
        },
        {"created_on": "2026-04-10", "name": "marketing_etl", "database_name": "PROD"},
        {"created_on": "2026-01-01", "name": "click_test", "database_name": "PROD"},
    ]


@pytest.fixture
def valid_task_history_data():
    """
    Valid task data, as would be returned from Database's
    get_task_history method.
    """
    return [
        {"QUERY_ID": "1", "NAME": "marketing_etl", "DATABASE_NAME": "PROD"},
        {"QUERY_ID": "3000", "NAME": "strip_metadata", "DATABASE_NAME": "PROD"},
        {"QUERY_ID": "210", "NAME": "click_test", "DATABASE_NAME": "PROD"},
    ]


@pytest.fixture
def dummy_database(monkeypatch):
    """
    Dummy Database that doesn't connect to Snowflake.
    """
    monkeypatch.setattr(Database, "connect_to_snowflake", Mock())
    monkeypatch.setattr(Database, "cursor", None, raising=False)
    return Database(credentials=None)


# Tests
async def test_switch_tab(monkeypatch):
    """
    Test pressing the S key switches the tab.
    """
    monkeypatch.setattr(SnowTask, "on_mount", Mock())
    app = SnowTask(None, None)
    async with app.run_test() as pilot:
        app.set_focus(app.query_one("#task_table"))
        await pilot.press("s")
        assert app.query_one(TabbedContent).active == "task_history"


async def test_refresh_data_works_no_preferences(
    monkeypatch, dummy_database, valid_task_data, valid_task_history_data
):
    """
    Test the refresh_data() method works as expected, when no preferences data
    has been provided by the user.
    """
    mock_get_tasks_method = Mock(return_value=valid_task_data)
    mock_get_task_history_method = Mock(return_value=valid_task_history_data)
    monkeypatch.setattr(dummy_database, "get_tasks", mock_get_tasks_method)
    monkeypatch.setattr(
        dummy_database, "get_task_history", mock_get_task_history_method
    )
    # Test:
    app = SnowTask(database=dummy_database, user_preferences=ConfigPreferences())
    async with app.run_test():
        # Test task table:
        task_table = app.query_one("#task_table")
        task_table_columns = [col.label.plain for col in task_table.ordered_columns]
        assert task_table_columns == [
            "created_on",
            "name",
            "database_name",
        ]
        task_table_rows = [
            task_table.get_row(row.key) for row in task_table.ordered_rows
        ]
        assert task_table_rows == [
            ["2026-03-19", "strip_metadata", "PROD"],
            ["2026-04-10", "marketing_etl", "PROD"],
            ["2026-01-01", "click_test", "PROD"],
        ]

        # Test task history table:
        task_history_table = app.query_one("#task_history_table")
        task_history_table_columns = [
            col.label.plain for col in task_history_table.ordered_columns
        ]
        assert task_history_table_columns == [
            "QUERY_ID",
            "NAME",
            "DATABASE_NAME",
        ]
        task_table_history_rows = [
            task_history_table.get_row(row.key)
            for row in task_history_table.ordered_rows
        ]
        assert task_table_history_rows == [
            ["1", "marketing_etl", "PROD"],
            ["3000", "strip_metadata", "PROD"],
            ["210", "click_test", "PROD"],
        ]


async def test_refresh_data_works_preferences_supplied(
    monkeypatch, dummy_database, valid_task_data, valid_task_history_data
):
    """
    Test the refresh_data() method works as expected, when preferences data
    has been provided by the user.
    """
    mock_get_tasks_method = Mock(return_value=valid_task_data)
    mock_get_task_history_method = Mock(return_value=valid_task_history_data)
    monkeypatch.setattr(dummy_database, "get_tasks", mock_get_tasks_method)
    monkeypatch.setattr(
        dummy_database, "get_task_history", mock_get_task_history_method
    )
    user_specified_columns = ConfigPreferences(
        tasks_columns={"created_on", "database_name"}, task_history_columns={"name"}
    )
    # Test:
    app = SnowTask(database=dummy_database, user_preferences=user_specified_columns)
    async with app.run_test():
        # Test task table:
        task_table = app.query_one("#task_table")
        task_table_columns = [col.label.plain for col in task_table.ordered_columns]
        assert task_table_columns == [
            "created_on",
            "database_name",
        ]
        task_table_rows = [
            task_table.get_row(row.key) for row in task_table.ordered_rows
        ]
        assert task_table_rows == [
            ["2026-03-19", "PROD"],
            ["2026-04-10", "PROD"],
            ["2026-01-01", "PROD"],
        ]

        # Test task history table:
        task_history_table = app.query_one("#task_history_table")
        task_history_table_columns = [
            col.label.plain for col in task_history_table.ordered_columns
        ]
        assert task_history_table_columns == [
            "NAME",
        ]
        task_table_history_rows = [
            task_history_table.get_row(row.key)
            for row in task_history_table.ordered_rows
        ]
        assert task_table_history_rows == [
            ["marketing_etl"],
            ["strip_metadata"],
            ["click_test"],
        ]


async def test_refresh_data_works_with_key_press(
    monkeypatch, dummy_database, valid_task_data, valid_task_history_data
):
    """
    Test the refresh_data() method works when R key is pressed.
    """
    mock_get_tasks_method = Mock(return_value=valid_task_data)
    mock_get_task_history_method = Mock(return_value=valid_task_history_data)
    monkeypatch.setattr(dummy_database, "get_tasks", mock_get_tasks_method)
    monkeypatch.setattr(
        dummy_database, "get_task_history", mock_get_task_history_method
    )
    # Test:
    app = SnowTask(database=dummy_database, user_preferences=ConfigPreferences())
    async with app.run_test() as pilot:
        await pilot.press("r")
        # Test task table:
        task_table = app.query_one("#task_table")
        task_table_columns = [col.label.plain for col in task_table.ordered_columns]
        assert task_table_columns == [
            "created_on",
            "name",
            "database_name",
        ]
        task_table_rows = [
            task_table.get_row(row.key) for row in task_table.ordered_rows
        ]
        assert task_table_rows == [
            ["2026-03-19", "strip_metadata", "PROD"],
            ["2026-04-10", "marketing_etl", "PROD"],
            ["2026-01-01", "click_test", "PROD"],
        ]

        # Test task history table:
        task_history_table = app.query_one("#task_history_table")
        task_history_table_columns = [
            col.label.plain for col in task_history_table.ordered_columns
        ]
        assert task_history_table_columns == [
            "QUERY_ID",
            "NAME",
            "DATABASE_NAME",
        ]
        task_table_history_rows = [
            task_history_table.get_row(row.key)
            for row in task_history_table.ordered_rows
        ]
        assert task_table_history_rows == [
            ["1", "marketing_etl", "PROD"],
            ["3000", "strip_metadata", "PROD"],
            ["210", "click_test", "PROD"],
        ]


async def test_sort_column(
    monkeypatch, dummy_database, valid_task_data, valid_task_history_data
):
    """
    Test pressing the A key sorts the selected column ascendin and pressing the
    D key sorts the selected column descending.
    """
    mock_get_tasks_method = Mock(return_value=valid_task_data)
    mock_get_task_history_method = Mock(return_value=valid_task_history_data)
    monkeypatch.setattr(dummy_database, "get_tasks", mock_get_tasks_method)
    monkeypatch.setattr(
        dummy_database, "get_task_history", mock_get_task_history_method
    )
    # Test:
    app = SnowTask(database=dummy_database, user_preferences=ConfigPreferences())
    async with app.run_test() as pilot:
        ### Task table ###
        task_table = app.query_one("#task_table")
        app.set_focus(task_table)
        await pilot.press("a")
        task_table_rows = [
            task_table.get_row(row.key) for row in task_table.ordered_rows
        ]
        assert task_table_rows == [
            ["2026-01-01", "click_test", "PROD"],
            ["2026-03-19", "strip_metadata", "PROD"],
            ["2026-04-10", "marketing_etl", "PROD"],
        ]
        await pilot.press("d")
        task_table_rows = [
            task_table.get_row(row.key) for row in task_table.ordered_rows
        ]
        assert task_table_rows == [
            ["2026-04-10", "marketing_etl", "PROD"],
            ["2026-03-19", "strip_metadata", "PROD"],
            ["2026-01-01", "click_test", "PROD"],
        ]
        ### Task history table ###
        task_history_table = app.query_one("#task_history_table")
        app.set_focus(task_history_table)
        await pilot.press("a")
        task_history_table_row = [
            task_history_table.get_row(row.key)
            for row in task_history_table.ordered_rows
        ]
        assert task_history_table_row == [
            ["1", "marketing_etl", "PROD"],
            ["210", "click_test", "PROD"],
            ["3000", "strip_metadata", "PROD"],
        ]
        await pilot.press("d")
        task_history_table_row = [
            task_history_table.get_row(row.key)
            for row in task_history_table.ordered_rows
        ]
        assert task_history_table_row == [
            ["3000", "strip_metadata", "PROD"],
            ["210", "click_test", "PROD"],
            ["1", "marketing_etl", "PROD"],
        ]


async def test_filter_data_key(
    monkeypatch, dummy_database, valid_task_data, valid_task_history_data
):
    """
    Test pressing F key opens and closes FilterInput.
    """
    mock_get_tasks_method = Mock(return_value=valid_task_data)
    mock_get_task_history_method = Mock(return_value=valid_task_history_data)
    monkeypatch.setattr(dummy_database, "get_tasks", mock_get_tasks_method)
    monkeypatch.setattr(
        dummy_database, "get_task_history", mock_get_task_history_method
    )
    app = SnowTask(database=dummy_database, user_preferences=ConfigPreferences())
    async with app.run_test() as pilot:
        app.set_focus(app.query_one("#task_table"))
        filter_input = app.query_one("#filter_input")
        await pilot.press("f")
        # Pressing the F key opens the filter input:
        assert filter_input.display
        # Pressing the F key again closes the filter:
        app.set_focus(app.query_one("#task_table"))
        await pilot.press("f")
        assert not filter_input.display


async def test_input_value_invalid(
    monkeypatch, dummy_database, valid_task_data, valid_task_history_data
):
    """
    Test an error message is printed if an invalid regex pattern is entered
    by the user.
    """
    mock_get_tasks_method = Mock(return_value=valid_task_data)
    mock_get_task_history_method = Mock(return_value=valid_task_history_data)
    monkeypatch.setattr(dummy_database, "get_tasks", mock_get_tasks_method)
    monkeypatch.setattr(
        dummy_database, "get_task_history", mock_get_task_history_method
    )
    app = SnowTask(database=dummy_database, user_preferences=ConfigPreferences())
    async with app.run_test() as pilot:
        app.set_focus(app.query_one("#task_table"))
        filter_input = app.query_one("#filter_input")
        app.set_focus(filter_input)
        filter_input.value = "[/"
        await pilot.press("enter")
        assert filter_input.value == "Invalid regex pattern. Try again."
        assert filter_input.cursor_at_end


@patch.object(TaskTable, "filter_data")
async def test_valid_input_value_passes_correct_data(
    mock_submit, monkeypatch, dummy_database, valid_task_data, valid_task_history_data
):
    """
    Test that if a valid regex pattern is entered by the user, the correct
    data is returned (column key and regex pattern).
    """
    mock_get_tasks_method = Mock(return_value=valid_task_data)
    mock_get_task_history_method = Mock(return_value=valid_task_history_data)
    monkeypatch.setattr(dummy_database, "get_tasks", mock_get_tasks_method)
    monkeypatch.setattr(
        dummy_database, "get_task_history", mock_get_task_history_method
    )
    app = SnowTask(database=dummy_database, user_preferences=ConfigPreferences())
    expected_to_pass = Filter(0, re.compile("marketing.*"))
    async with app.run_test() as pilot:
        task_table = app.query_one("#task_table")
        app.set_focus(task_table)
        filter_input = app.query_one("#filter_input")
        app.set_focus(filter_input)
        filter_input.value = "marketing.*"
        await pilot.press("enter")
        mock_submit.assert_called_once_with(expected_to_pass)


async def test_filter_data_works(
    monkeypatch, dummy_database, valid_task_data, valid_task_history_data
):
    """
    Test that TaskTable's refresh_data() correctly filters rows.
    """
    mock_get_tasks_method = Mock(return_value=valid_task_data)
    mock_get_task_history_method = Mock(return_value=valid_task_history_data)
    monkeypatch.setattr(dummy_database, "get_tasks", mock_get_tasks_method)
    monkeypatch.setattr(
        dummy_database, "get_task_history", mock_get_task_history_method
    )
    expected_return_value = [list(row.values()) for row in valid_task_data]
    app = SnowTask(database=dummy_database, user_preferences=ConfigPreferences())
    async with app.run_test() as pilot:
        task_table = app.query_one("#task_table")
        app.set_focus(task_table)
        filter_input = app.query_one("#filter_input")
        app.set_focus(filter_input)
        filter_input.value = "2026-0[1|3].*"  # Regex pattern
        await pilot.press("enter")
        task_table = app.query_one("#task_table")
        expected_return_value = [list(row.values()) for row in valid_task_data]
        assert task_table.unfiltered_rows == expected_return_value
        task_table_rows = [
            task_table.get_row(row.key) for row in task_table.ordered_rows
        ]
        assert task_table_rows == [
            ["2026-03-19", "strip_metadata", "PROD"],
            ["2026-01-01", "click_test", "PROD"],
        ]


async def test_filter_data_does_not_apply_if_no_match(
    monkeypatch, dummy_database, valid_task_data, valid_task_history_data
):
    """
    Test that TaskTable's refresh_data() does not filter data
    if no rows match the pattern.
    """
    mock_get_tasks_method = Mock(return_value=valid_task_data)
    mock_get_task_history_method = Mock(return_value=valid_task_history_data)
    monkeypatch.setattr(dummy_database, "get_tasks", mock_get_tasks_method)
    monkeypatch.setattr(
        dummy_database, "get_task_history", mock_get_task_history_method
    )
    expected_return_value = [list(row.values()) for row in valid_task_data]
    app = SnowTask(database=dummy_database, user_preferences=ConfigPreferences())
    async with app.run_test() as pilot:
        task_table = app.query_one("#task_table")
        app.set_focus(task_table)
        filter_input = app.query_one("#filter_input")
        app.set_focus(filter_input)
        filter_input.value = "no_match"  # Regex pattern
        await pilot.press("enter")
        task_table = app.query_one("#task_table")
        expected_return_value = [list(row.values()) for row in valid_task_data]
        assert task_table.unfiltered_rows == expected_return_value
        task_table_rows = [
            task_table.get_row(row.key) for row in task_table.ordered_rows
        ]
        assert task_table_rows == [
            ["2026-03-19", "strip_metadata", "PROD"],
            ["2026-04-10", "marketing_etl", "PROD"],
            ["2026-01-01", "click_test", "PROD"],
        ]


async def test_clear_filter_works(
    monkeypatch, dummy_database, valid_task_data, valid_task_history_data
):
    """
    Test that clearing the table of filtered data works.
    """
    mock_get_tasks_method = Mock(return_value=valid_task_data)
    mock_get_task_history_method = Mock(return_value=valid_task_history_data)
    monkeypatch.setattr(dummy_database, "get_tasks", mock_get_tasks_method)
    monkeypatch.setattr(
        dummy_database, "get_task_history", mock_get_task_history_method
    )
    expected_return_value = [list(row.values()) for row in valid_task_data]
    app = SnowTask(database=dummy_database, user_preferences=ConfigPreferences())
    async with app.run_test() as pilot:
        task_table = app.query_one("#task_table")
        app.set_focus(task_table)
        filter_input = app.query_one("#filter_input")
        app.set_focus(filter_input)
        filter_input.value = "2026-0[1|3].*"  # Regex pattern
        await pilot.press("enter")
        task_table = app.query_one("#task_table")
        expected_return_value = [list(row.values()) for row in valid_task_data]
        assert task_table.unfiltered_rows == expected_return_value
        task_table_rows = [
            task_table.get_row(row.key) for row in task_table.ordered_rows
        ]
        assert task_table_rows == [
            ["2026-03-19", "strip_metadata", "PROD"],
            ["2026-01-01", "click_test", "PROD"],
        ]
        app.set_focus(filter_input)
        filter_input.value = "2026-03-19.*"  # Regex pattern
        await pilot.press("enter")
        await pilot.press("c")
        task_table_rows = [
            task_table.get_row(row.key) for row in task_table.ordered_rows
        ]
        assert task_table_rows == [
            ["2026-03-19", "strip_metadata", "PROD"],
            ["2026-04-10", "marketing_etl", "PROD"],
            ["2026-01-01", "click_test", "PROD"],
        ]
