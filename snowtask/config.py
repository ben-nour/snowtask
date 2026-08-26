"""
config.py
"""

import dataclasses
import os

import yaml

VALID_COLUMNS = {
    "tasks": {
        "created_on",
        "name",
        "id",
        "database_name",
        "schema_name",
        "owner",
        "comment",
        "warehouse",
        "schedule",
        "predecessors",
        "state",
        "definition",
        "condition",
        "allow_overlapping_execution",
        "error_integration",
        "last_committed_on",
        "last_suspended_on",
        "owner_role_type",
        "config",
        "task_relations",
        "last_suspended_reason",
        "success_integration",
        "scheduling_mode",
        "target_completion_interval",
        "execute_as_user",
        "overlap_policy",
        "created_by_user",
    },
    "task_history": {
        "query_id",
        "name",
        "database_name",
        "schema_name",
        "query_text",
        "condition_text",
        "state",
        "error_code",
        "error_message",
        "scheduled_time",
        "query_start_time",
        "next_scheduled_time",
        "completed_time",
        "root_task_id",
        "graph_version",
        "run_id",
        "return_value",
        "scheduled_from",
        "attempt_number",
        "config",
        "query_hash",
        "query_hash_version",
        "query_parameterized_hash",
        "query_parameterized_hash_version",
        "graph_run_group_id",
        "backfill_info",
        "spcs_job_id",
        "scheduled_by_user",
    },
}


@dataclasses.dataclass
class ConfigPreferences:
    """
    Column preference specified by user in config file.
    """

    tasks_columns: set[str] | None = None
    task_history_columns: set[str] | None = None


class ConfigFileError(Exception):
    """The configuration file contains invalid or unsupported values."""

    def __init__(
        self,
        invalid_keys=None,
        invalid_column=None,
        yaml_scanner_error=None,
    ):
        super().__init__()
        self.invalid_keys = invalid_keys
        self.invalid_column = invalid_column
        self.yaml_scanner_error = yaml_scanner_error


def get_config_file() -> dict[str, str] | None:
    """
    Get Snowtask config file, if it exists.
    """
    if config_file_path := os.getenv("SNOWTASK_CONFIG_FILE"):
        with open(config_file_path, mode="r", encoding="utf-8") as f:
            try:
                yaml_file = yaml.safe_load(f)
                return yaml_file
            except yaml.scanner.ScannerError as e:
                raise ConfigFileError(yaml_scanner_error=e.problem) from e
    return None


def parse_config_file(yaml_contents: dict | None) -> ConfigPreferences:
    """
    Parse config file for valid columns.
    """
    config_preferences = ConfigPreferences()
    if yaml_contents:
        # Check keys:
        if not_valid_keys := [
            key for key in yaml_contents if key not in ("tasks", "task_history")
        ]:
            raise ConfigFileError(invalid_keys=not_valid_keys)
        # Check and get columns:
        for index, data_set in enumerate(("tasks", "task_history")):
            if raw_columns_data := yaml_contents.get(data_set):
                specified_columns = []
                for col in raw_columns_data:
                    if col.lower() not in VALID_COLUMNS[data_set]:
                        raise ConfigFileError(invalid_column=col)
                    specified_columns.append(col.lower())
                if index == 0:  # First row of Snowflake returned data are column names.
                    config_preferences.tasks_columns = set(specified_columns)
                    continue
                config_preferences.task_history_columns = set(specified_columns)
    return config_preferences
