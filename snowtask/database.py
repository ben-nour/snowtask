"""
The Snowflake database.
"""

import snowflake.connector


class Database:
    """
    The Snowflake database.
    """

    def __init__(self, credentials: dict):
        self.credentials = credentials
        self.connection = self.connect_to_snowflake(credentials)
        self.cursor = self.connection.cursor(snowflake.connector.DictCursor)

    def connect_to_snowflake(
        self,
        credentials: dict,
    ) -> snowflake.connector.SnowflakeConnection:
        """
        Connect to Snowflake.
        """
        return snowflake.connector.connect(**credentials)

    def get_tasks(self) -> list[dict]:
        """
        Get tasks.
        """
        self.cursor.execute("SHOW TASKS ;")
        return self.cursor.fetchall()

    def get_task_history(self) -> list[dict]:
        self.cursor.execute("SELECT * FROM TABLE(INFORMATION_SCHEMA.task_history());")
        return self.cursor.fetchall()
