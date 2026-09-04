"""
Snowtask CLI.
"""

import argparse
import os

from rich_argparse import RichHelpFormatter


class CLIError(Exception):
    """
    Environmental variable not found.
    """

    def __init__(self, missing_env):
        super().__init__()
        self.missing_env = missing_env


def get_parser_args() -> dict:  # pragma: no cover
    """
    Create the command-line parser and get arguments.
    """
    parser = argparse.ArgumentParser(
        description="Inspect your Snowflake Tasks from the commmand-line.",
        formatter_class=RichHelpFormatter,
    )
    parser.add_argument(
        "-a",
        "--account",
        help="Your Snowflake account name. Environmental variable: [purple]SNOWFLAKE_ACCOUNT_NAME[/purple]",
        required=False,
    )
    parser.add_argument(
        "-u",
        "--user",
        help="Your Snowflake username. Environmental variable: [purple]SNOWFLAKE_USER[/purple]",
        required=False,
    )
    parser.add_argument(
        "-p",
        "--password",
        help="Your Snowflake password. Environmental variable: [purple]SNOWFLAKE_PASSWORD[/purple]",
        required=False,
    )
    parser.add_argument(
        "-at",
        "--authenticator",
        help="Your Snowflake authenticator method. Environmental variable: [purple]SNOWFLAKE_AUTHENTICATOR[/purple]",
        required=False,
    )
    parser.add_argument(
        "-t",
        "--token",
        help="YourOAuth access token. Environmental variable: [purple]SNOWFLAKE_TOKEN[/purple]",
        required=False,
    )
    parser.add_argument(
        "-d",
        "--database",
        help="Your Snowflake database name. Environmental variable: [purple]SNOWFLAKE_DATABASE[/purple]",
        required=False,
    )
    parser.add_argument(
        "-r",
        "--role",
        help="Your Snowflake role. Environmental variable: [purple]SNOWFLAKE_ROLE[/purple]",
        required=False,
    )
    parser.add_argument(
        "-s",
        "--schema",
        type=str,
        help="Your Snowflake schema name. Environmental variable: [purple]SNOWFLAKE_SCHEMA[/purple]",
        required=False,
    )
    parser.add_argument(
        "-w",
        "--warehouse",
        help="Your Snowflake warehouse name. Environmental variable: [purple]SNOWFLAKE_WAREHOUSE[/purple]",
        required=False,
    )
    args = vars(parser.parse_args()).copy()
    return args


def get_credentials(cli_arguments: dict) -> dict:
    """
    Get user's Snowflake credentials.
    """
    env_variables = {
        "account": "SNOWFLAKE_ACCOUNT",
        "user": "SNOWFLAKE_USER",
        "password": "SNOWFLAKE_PASSWORD",
        "authenticator": "SNOWFLAKE_AUTHENTICATOR",
        "token": "SNOWFLAKE_TOKEN",
        "database": "SNOWFLAKE_DATABASE",
        "role": "SNOWFLAKE_ROLE",
        "schema": "SNOWFLAKE_SCHEMA",
        "warehouse": "SNOWFLAKE_WAREHOUSE",
    }
    credentials = {}
    for parameter, value in cli_arguments.items():
        # Check CLI arguments first.
        if value is not None:
            credentials[parameter] = value
            continue
        # Check global envs.
        env_variable_to_check = env_variables[parameter]
        env_value = os.getenv(env_variable_to_check, None)
        credentials[parameter] = env_value
        if parameter in {"account", "user"} and not env_value:
            raise CLIError(env_variable_to_check)
    # Check password has been provided (if needed):
    if not credentials.get("password") and credentials.get("authenticator") in {
        "password",
        None,
    }:
        raise CLIError("SNOWFLAKE_PASSWORD")
    return credentials
