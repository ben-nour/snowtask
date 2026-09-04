"""
Snowtask.
"""

import asyncio
import collections
import datetime
import re

from textual.app import App, ComposeResult
from textual.widgets import (
    DataTable,
    Footer,
    Input,
    Label,
    TabbedContent,
    TabPane,
    Tabs,
)

from snowtask.config import ConfigPreferences
from snowtask.database import Database

Filter = collections.namedtuple("Filter", ["col_index", "regex_pattern"])


class TaskTable(DataTable):
    """
    A DataTable with Snowflake task data.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "Data"
        self.zebra_stripes = True
        self.unfiltered_rows = None

    def add_data(self, tabular_data: list, columns_to_include: set | None) -> None:
        """
        Add processed data to table.
        """
        self.clear(columns=True)
        # Delete columns not specified in config file:
        if columns_to_include:
            new_task_data = []
            for row in tabular_data:
                new_row = {}
                for key, value in row.items():
                    # Note task history raw column headers are uppercase:
                    if key.lower() in columns_to_include:
                        new_row[key] = value
                new_task_data.append(new_row)
            tabular_data = new_task_data
        # Prep data to be added to table.
        columns = tuple(
            tabular_data[0].keys()
        )  # First row is all that's needed to get column headers.
        rows = [list(row.values()) for row in tabular_data]
        # Add data to table.
        self.add_columns(*columns)
        self.add_rows(rows)
        self.unfiltered_rows = rows
        self.border_subtitle = f"Last refreshed at [white]{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}[/white] (local time)"

    def sort_column(self, direction: bool = False) -> None:
        """
        Sort column values.
        """
        _, column_key = self.coordinate_to_cell_key(self.cursor_coordinate)
        self.sort(
            column_key,
            key=lambda column_key: (column_key is not None, column_key),
            reverse=direction,
        )

    def filter_data(self, filter_details: Filter) -> None:
        """
        Filter data in column n, based on regex supplied.
        """
        self.loading = True
        current_rows = [self.get_row(row.key) for row in self.ordered_rows]
        # Filter data:
        pattern = filter_details.regex_pattern
        filtered_rows = [
            row
            for row in current_rows
            if row[filter_details.col_index]  # None objects break fullmatch()
            if pattern.fullmatch(str(row[filter_details.col_index]))
        ]
        if filtered_rows:  # Don't want to apply filtering if no rows match.
            self.clear()
            self.add_rows(filtered_rows)
        self.loading = False

    def clear_filtering(self) -> None:
        """
        Clear filtering from data.
        """
        self.loading = True
        self.clear()
        self.add_rows(self.unfiltered_rows)
        self.loading = False


class FilterInput(Input):
    """
    Input to filter table data.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "Filter"
        self.display = False
        self.type = "text"
        self.placeholder = "Enter your regex here"


class SnowTask(App):
    """
    A TUI to manage Snowflake Tasks.
    """

    CSS = """
        DataTable {
            border: round $accent;
            height: 1fr;
            border-title-align: left;
        }

        Input {
            border: round $accent;
            border-title-align: center;
            border-title-color: white;
        }

        TabbedContent {
            height: 1fr;
        }

        TabPane {
            height: 1fr;
        }

        Label {
        margin-bottom: 1;}
    """
    BINDINGS = [
        ("s", "show_tab()", "Switch tab"),
        ("r", "refresh_data_tables", "Refresh data"),
        ("f", "show_filter_input()", "Filter data"),
        ("c", "clear_filtering()", "Clear filtering"),
        ("a", "sort_column()", "Sort column (asc)"),
        ("d", "sort_column_desc()", "Sort column (desc)"),
        (
            "q",
            "quit",
        ),
    ]
    ENABLE_COMMAND_PALETTE = False

    def __init__(self, database: Database, user_preferences: ConfigPreferences):
        super().__init__()
        self.theme = "flexoki"
        self.database = database
        self.user_preferences = user_preferences
        self.id = "app"

    def compose(self) -> ComposeResult:
        yield Label("[#9B76C8][bold]SnowTask[/bold][/#9B76C8][#9B76C8 50%] 0.1.0")
        with TabbedContent(initial="tasks"):
            with TabPane("Tasks", id="tasks"):
                yield TaskTable(id="task_table")
            with TabPane("Task History", id="task_history"):
                yield TaskTable(
                    id="task_history_table",
                )
        yield Footer()
        yield FilterInput(id="filter_input")

    def on_mount(self):
        self.call_later(self.action_refresh_data_tables)
        task_table = self.query_one("#task_table", TaskTable)
        self.set_focus(task_table)

    def action_show_tab(self) -> None:
        """Switch to a new tab."""
        self.query_one(Tabs).action_next_tab()

    def key_enter(self):
        """
        Focus on TaskTable in view when Enter key pressed.
        """
        if active_pane := self.query_one(TabbedContent).active_pane:
            active_table = active_pane.query_one(TaskTable)
            self.set_focus(active_table)

    def action_show_filter_input(self) -> None:
        """
        Show/hide the FilterInput widget.
        """
        filter_input = self.query_one("#filter_input", FilterInput)
        if filter_input.display is False:
            filter_input.display = True
            self.set_focus(filter_input)
        else:
            filter_input.display = False
            filter_input.value = ""

    def on_input_submitted(self, event: FilterInput.Submitted) -> None:
        """
        Submit the regex pattern to filter data.
        """
        if filter_input := self.query_one("#filter_input", FilterInput):
            if user_raw_input := filter_input.value:
                # Validate valid regex:
                try:
                    user_input = re.compile(user_raw_input)
                except re.PatternError:
                    filter_input.value = "Invalid regex pattern. Try again."
                    filter_input.action_end()
                    return
                # Filter data
                if active_pane := self.query_one(TabbedContent).active_pane:
                    active_table = active_pane.query_one(TaskTable)
                    self.set_focus(active_table)  # Important this happens first.
                    cursor_column = active_table.cursor_column
                    user_filter_value = Filter(
                        col_index=cursor_column, regex_pattern=user_input
                    )
                    active_table.filter_data(user_filter_value)
                    filter_input.value = ""

    async def action_refresh_data_tables(self) -> None:
        """
        Refresh data on both tables.
        """
        if active_pane := self.query_one(TabbedContent).active_pane:
            active_table = active_pane.query_one(TaskTable)
            active_table.loading = True
            # Get new data
            task_data = await asyncio.to_thread(self.database.get_tasks)
            task_history_data = await asyncio.to_thread(self.database.get_task_history)
            # Refresh tables.
            task_table = self.query_one("#task_table", TaskTable)
            task_history_table = self.query_one("#task_history_table", TaskTable)
            task_table.add_data(
                tabular_data=task_data,
                columns_to_include=self.user_preferences.tasks_columns,
            )
            task_history_table.add_data(
                tabular_data=task_history_data,
                columns_to_include=self.user_preferences.task_history_columns,
            )
            active_table.loading = False

    def action_clear_filtering(self) -> None:
        """
        Clear any filtering applied to the table.
        """
        if active_pane := self.query_one(TabbedContent).active_pane:
            active_table = active_pane.query_one(TaskTable)
            active_table.clear_filtering()

    def action_sort_column(self) -> None:
        """
        Sort the column in which the cursor is placed.
        """
        if active_pane := self.query_one(TabbedContent).active_pane:
            active_table = active_pane.query_one(TaskTable)
            active_table.sort_column()

    def action_sort_column_desc(self) -> None:
        """
        Sort the column in which the cursor is placed.
        """
        if active_pane := self.query_one(TabbedContent).active_pane:
            active_table = active_pane.query_one(TaskTable)
            active_table.sort_column(True)
