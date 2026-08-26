"""
Unit tests for config.py
"""

from unittest.mock import mock_open, patch

import pytest

from snowtask.config import (
    ConfigFileError,
    ConfigPreferences,
    get_config_file,
    parse_config_file,
)


### get_config_file() tests ###
@patch.dict("os.environ", {}, clear=True)
def test_get_config_file_does_nothing_if_no_variable_exists():
    """
    Test that get_config_file() doesn't do anything (raise exception or return a value other than None)
    if the SNOWTASK_CONFIG_FILE variable can't be found.
    """
    assert get_config_file() is None


@patch.dict("os.environ", {"SNOWTASK_CONFIG_FILE": ""}, clear=True)
def test_get_config_file_does_nothing_if_variable_empty():
    """
    Test that get_config_file() doesn't do anything (raise exception or return a value other than None)
    if the SNOWTASK_CONFIG_FILE variable is empty.
    """
    assert get_config_file() is None


@patch.dict(
    "os.environ", {"SNOWTASK_CONFIG_FILE": "User/ben/snowtask_config.yml"}, clear=True
)
@patch("builtins.open", mock_open(read_data="""task: [created_on,]"""))
def test_get_config_file_returns_dictionary():
    """
    Test that get_config_file() returns a dictionary.
    """
    assert get_config_file() == {"task": ["created_on"]}


@patch.dict(
    "os.environ", {"SNOWTASK_CONFIG_FILE": "User/ben/snowtask_config.yml"}, clear=True
)
@patch("builtins.open", mock_open(read_data=""))
def test_get_config_file_returns_none_if_yaml_empty():
    """
    Test that get_config_file() returns a dictionary.
    """
    assert get_config_file() is None


@patch.dict(
    "os.environ", {"SNOWTASK_CONFIG_FILE": "User/ben/snowtask_config.yml"}, clear=True
)
@patch(
    "builtins.open",
    mock_open(
        read_data="""tasks: ["created_on"]
task_history"""
    ),
)  # No colon.
def test_get_config_file_prints_error_if_yaml_invalid():
    """
    Test that get_config_file() prints an error message
    if YAML file has incorrect syntax.
    """
    with pytest.raises(ConfigFileError):
        get_config_file()


### parse_config_file() tests ###
def test_parse_config_file_raises_error_invalid_keys():
    """
    Test that parse_config_file() raises an error if the keys are invalid.
    """
    with pytest.raises(ConfigFileError):
        parse_config_file({"settings": ["syntax_on"]})


def test_parse_config_file_raises_error_invalid_task_columns():
    """
    Test that parse_config_file() raises an error if the task columns specified
    do not exist.
    """
    with pytest.raises(ConfigFileError) as exc_info:
        parse_config_file({"tasks": ["created_on", "runtime"]})
    assert exc_info.value.invalid_column == "runtime"

    with pytest.raises(ConfigFileError) as exc_info:
        parse_config_file({"task_history": ["query_id", "query_fake_id"]})
    assert exc_info.value.invalid_column == "query_fake_id"


def test_parse_config_file_returns_empty_config():
    """
    Test that parse_config_file() returns an empty ConfigPreferences
    instance if there is no Snowtask config file.
    """
    user_preference = parse_config_file(None)
    assert isinstance(user_preference, ConfigPreferences)
    assert user_preference.tasks_columns is None
    assert user_preference.task_history_columns is None


def test_parse_config_file_returns_correct_data():
    """
    Test that parse_config_file() returns the expected data.
    """
    user_preference = parse_config_file({"task_history": ["QUERY_ID", "DATABASE_NAME"]})
    assert isinstance(user_preference, ConfigPreferences)
    assert user_preference.task_history_columns == {"query_id", "database_name"}

    user_preference = parse_config_file({"tasks": ["created_on"]})
    assert isinstance(user_preference, ConfigPreferences)
    assert user_preference.tasks_columns == {"created_on"}

    user_preference = parse_config_file({"task_history": ["query_id", "database_name"]})
    assert isinstance(user_preference, ConfigPreferences)
    assert user_preference.task_history_columns == {"query_id", "database_name"}

    user_preference = parse_config_file(
        {
            "tasks": ["schema_name", "definition"],
            "task_history": ["error_code"],
        }
    )
    assert isinstance(user_preference, ConfigPreferences)
    assert user_preference.tasks_columns == {"schema_name", "definition"}
    assert user_preference.task_history_columns == {"error_code"}

    # Mix-matching casing in config file:
    user_preference = parse_config_file({"task_history": ["QUERY_ID", "database_name"]})
    assert isinstance(user_preference, ConfigPreferences)
    assert user_preference.task_history_columns == {"query_id", "database_name"}
