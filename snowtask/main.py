"""
Snowtask entry point script.
"""

from rich import print as rich_print

from .app import SnowTask
from .cli import CLIError, get_credentials, get_parser_args
from .config import ConfigFileError, get_config_file, parse_config_file
from .database import Database


def main() -> int:
    """
    Run the app.
    """
    try:
        user_preferences = parse_config_file(get_config_file())
        credentials = get_credentials(get_parser_args())
    except ConfigFileError as error:
        if error.yaml_scanner_error:
            rich_print(
                f"[bold red]Error[/bold red]: invalid YAML in config file: {error.yaml_scanner_error}"
            )
        elif error.invalid_keys:
            rich_print(
                f"[bold red]Error[/bold red]: Invalid keys in configuration file: [orange3]{error.invalid_keys}[/orange3]"
            )
        else:
            rich_print(
                f"[bold red]Error[/bold red]: Invalid column specified in configuration file: [orange3]{error.invalid_column}[/orange3]"
            )
        return 1
    except CLIError as error:
        rich_print(
            f"[bold red]Error[/bold red]: Couldn't find the environmental variable [orange3]{error.missing_env}[/orange3]. Create this env variable or pass an argument to the CLI. This is a required parameter."
        )
        return 1
    app = SnowTask(database=Database(credentials), user_preferences=user_preferences)
    app.run()
    return app.return_code or 0


if __name__ == "__main__":
    raise SystemExit(main())
