"""
Unit tests for cli.py
"""

from unittest.mock import patch

import pytest

from snowtask.cli import CLIError, get_credentials


# Fixtures
@pytest.fixture
def empty_cli_arguments():
    """
    Empty CLI arguments fixture.
    """
    return {
        "account": None,
        "user": None,
        "password": None,
        "authenticator": None,
        "token": None,
        "database": None,
        "role": None,
        "schema": None,
        "warehouse": None,
    }


# Unit tests
@patch.dict("os.environ", {}, clear=True)
def test_get_credentials_no_password_throws_error():
    """
    Test that get_credentials() prints an error message and exits the program
    if no password is provided.
    """
    cli_arguments = {
        "account": "westworld",
        "user": "ben",
        "password": None,
        "authenticator": None,
        "token": None,
        "database": None,
        "role": None,
        "schema": None,
        "warehouse": None,
    }
    with pytest.raises(CLIError):
        get_credentials(cli_arguments)


@patch.dict("os.environ", {}, clear=True)
def test_get_credentials_password_not_needed():
    """
    Test that get_credentials() doesn't need a password passed via CLI
    argument or env variable if authenticator method has been specified
    as external browser.
    """
    cli_values = {
        "account": "westworld",
        "user": "ben",
        "password": None,
        "authenticator": "externalBrowser",
        "token": None,
        "database": None,
        "role": None,
        "schema": None,
        "warehouse": None,
    }
    assert get_credentials(cli_values) == cli_values


@patch.dict(
    "os.environ",
    {
        "SNOWFLAKE_USER": "ben",
        "SNOWFLAKE_DATABASE": "prod",
    },
    clear=True,
)
def test_get_credentials_uses_cli_values():
    """
    Test get_credentials() uses the CLI arguments passed to it, even if
    env variables are non-empty.
    """
    cli_values = {
        "account": "westworld",
        "user": "jane",
        "password": None,
        "authenticator": "externalBrowser",
        "token": None,
        "database": "dev",
        "role": "analyst",
        "schema": "public",
        "warehouse": None,
    }
    assert get_credentials(cli_values) == cli_values


@patch.dict(
    "os.environ",
    {
        "SNOWFLAKE_ACCOUNT": "westworld",
        "SNOWFLAKE_USER": "ben",
        # "SNOWFLAKE_PASSWORD":
        "SNOWFLAKE_AUTHENTICATOR": "externalBrowser",
        "SNOWFLAKE_DATABASE": "prod",
        "SNOWFLAKE_ROLE": "analyst",
        "SNOWFLAKE_SCHEMA": "public",
        "SNOWFLAKE_WAREHOUSE": "analytics",
    },
    clear=True,
)
def test_get_credentials_uses_env_variables(empty_cli_arguments):
    """
    Test get_credentials() uses environmental variables if no CLI arguments
    are passed to it.
    """
    expected_values = {
        "account": "westworld",
        "user": "ben",
        "password": None,
        "authenticator": "externalBrowser",
        "token": None,
        "database": "prod",
        "role": "analyst",
        "schema": "public",
        "warehouse": "analytics",
    }
    assert get_credentials(empty_cli_arguments) == expected_values


@patch.dict("os.environ", {}, clear=True)
def test_get_credentials_missing_env_variable_throws_error(empty_cli_arguments):
    """
    Test an error messsage is printed and program exited if no required cli argument
    is passed and environmental variable doesn't exist.
    """
    with pytest.raises(CLIError):
        get_credentials(empty_cli_arguments)


@patch.dict(
    "os.environ",
    {
        "SNOWFLAKE_ACCOUNT": "westworld",
        "SNOWFLAKE_PASSWORD": "password123",
    },
    clear=True,
)
def test_get_credentials_missing_account_and_user_variables_throws_error(
    empty_cli_arguments,
):
    """
    Test an error messsage is printed and program exited if no required cli argument
    is passed and environmental variable doesn't exist.
    """
    with pytest.raises(CLIError):
        get_credentials(empty_cli_arguments)


@patch.dict(
    "os.environ",
    {"SNOWFLAKE_DATABASE": "dev", "SNOWFLAKE_USER": "jane"},
    clear=True,
)
def test_get_credentials_uses_cli_and_envs():
    """
    Test get_credentials() will use both passed CLI arguments and environmental.
    """
    cli_values = {
        "account": "westworld",
        "user": None,
        "password": None,
        "authenticator": "externalBrowser",
        "token": None,
        "database": None,
        "role": "analyst",
        "schema": "public",
        "warehouse": "analytics",
    }
    expected_values = {
        "account": "westworld",
        "user": "jane",
        "password": None,
        "authenticator": "externalBrowser",
        "token": None,
        "database": "dev",
        "role": "analyst",
        "schema": "public",
        "warehouse": "analytics",
    }
    assert get_credentials(cli_values) == expected_values
