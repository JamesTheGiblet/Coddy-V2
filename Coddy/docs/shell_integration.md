# Coddy Shell Integration

To make invoking Coddy's features quicker from the terminal, you can use shell aliases and functions. This allows you to type a short command like `coddy` instead of `python /path/to/your/project/Coddy/main.py`.

Below are examples for popular shells.

## Prerequisites

For the function wrappers to work robustly, it's recommended to set an environment variable `CODDY_HOME` that points to the root directory of your Coddy project.

For example, in Bash/Zsh:
```bash
export CODDY_HOME="/path/to/your/project/Coddy"
```

In Fish:
```fish
set -x CODDY_HOME "/path/to/your/project/Coddy"
```

In PowerShell:
```powershell
$env:CODDY_HOME = "/path/to/your/project/Coddy"
# To make it permanent, add it to your $PROFILE script.
```

## Bash / Zsh

Add the following to your `~/.bashrc` or `~/.zshrc` file:

```bash
# Coddy Shell Wrapper
coddy() {
    # Check if CODDY_HOME is set
    if [ -z "$CODDY_HOME" ]; then
        echo "CODDY_HOME environment variable is not set. Please set it to the root of your Coddy project." >&2
        return 1
    fi

    local main_script="$CODDY_HOME/main.py"
    if [ ! -f "$main_script" ]; then
        echo "Coddy main script not found at: $main_script" >&2
        return 1
    fi

    # Use the project's virtual environment if it exists
    local python_executable="python3"
    if [ -d "$CODDY_HOME/.venv" ]; then
        python_executable="$CODDY_HOME/.venv/bin/python"
    fi

    # Execute Coddy with all passed arguments
    "$python_executable" "$main_script" "$@"
}
```

## Fish Shell

Add the following to your `~/.config/fish/config.fish` file:

```fish
# Coddy Shell Wrapper
function coddy
    if not set -q CODDY_HOME
        echo "CODDY_HOME environment variable is not set. Please set it to the root of your Coddy project." >&2
        return 1
    end

    set -l main_script "$CODDY_HOME/main.py"
    if not test -f "$main_script"
        echo "Coddy main script not found at: $main_script" >&2
        return 1
    end

    # Use the project's virtual environment if it exists
    set -l python_executable "python3"
    if test -d "$CODDY_HOME/.venv"
        set python_executable "$CODDY_HOME/.venv/bin/python"
    end

    # Execute Coddy with all passed arguments
    "$python_executable" "$main_script" $argv
end
```

## PowerShell

Add the following to your PowerShell profile (you can find its path by running `$PROFILE`):

```powershell
function coddy {
    if (-not (Test-Path Env:CODDY_HOME)) {
        Write-Error "CODDY_HOME environment variable is not set. Please set it to the root of your Coddy project."
        return
    }
    python "$env:CODDY_HOME\main.py" $args
}
```

After adding the function to your profile, reload it (e.g., `. $PROFILE`) or restart your shell session.