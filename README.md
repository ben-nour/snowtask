<h1 align=center> ❄️snowtask❄️ </h2>

`snowtask` is a TUI for viewing information about your [Snowflake Tasks](https://docs.snowflake.com/en/user-guide/tasks-intro):


## Installation

```sh
pip install snowtask
```

You'd probably find it more useful to install via [pipx](https://github.com/pypa/pipx) so you can use
anywhere:

```sh
pipx install snowtask
```

## Usage

> [!WARNING]
>  `snowtask` executes the queries `SHOW TASKS ;` and `SELECT * FROM INFORMATION_SCHEMA.TASK_HISTORY()` on launch and if you press the Refresh data key, which will consume Snowflake credits.

### Authentication

To connect to Snowflake via this tool you can authenticate via SSO, password or OAuth. If there’s appetite for authentication via key-pairs or MFA I can add these options in a future release (please raise an issue if you want this).

To authenticate you must pass your account name and user via command-line arguments or you can populate the environmental variables `SNOWFLAKE_ACCOUNT` and `SNOWFLAKE_USER`.

```sh
snowtask --account westworld.us-east-2.aws --user ben --authentication externalBrowser
```

For a full list of parameters/arguments and their corresponding environmental variable names run `snowtask --help`

### Customising the tables

If you only want certain columns to display in `snowtask` you can specify this in a configuration file.

Create an environmental variable called `SNOWTASK_CONFIG_FILE` and point it to a YAML file:

```yml
# The columns you want displayed with the Tasks table:
tasks: ["created_on", "name", "database_name", "schema_name", "created_by]

# The columns you want displayed with the Task History table:
task_history: ["name", "scheduled_time", "state", "error_message]
```
