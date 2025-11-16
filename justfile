# Default recipe - show available commands
default:
    @just --list

format:
    cd apps/racing-coach-client && uvx ruff format src/ tests/
    cd apps/racing-coach-server && uvx ruff format src/ tests/
    cd libs/racing-coach-core && uvx ruff format src/ tests/

sort:
    cd apps/racing-coach-client && uvx ruff check src/ tests/ --select I --fix
    cd apps/racing-coach-server && uvx ruff check src/ tests/ --select I --fix
    cd libs/racing-coach-core && uvx ruff check src/ tests/ --select I --fix

sf:
    just sort
    just format


testapp app subdir="tests/" *args:
    cd apps/{{app}} && uv run pytest {{args}} {{subdir}}

testlib lib subdir="tests/" *args:
    cd libs/{{lib}} && uv run pytest {{args}} {{subdir}}

# Sync all projects
sync-all *args:
    @echo "Syncing racing-coach-core..."
    cd libs/racing-coach-core && uv sync {{args}}
    @echo "Syncing racing-coach-client..."
    cd apps/racing-coach-client && uv sync {{args}}
    @echo "Syncing racing-coach-server..."
    cd apps/racing-coach-server && uv sync {{args}}
    @echo "✓ All projects synced!"

# Sync specific project
sync project:
    @echo "Syncing {{project}}..."
    cd {{project}} && uv sync

# Run client
run-client:
    cd apps/racing-coach-client && uv run python -m racing_coach_client.app

# Run server
run-server:
    cd apps/racing-coach-server && uv run python -m racing_coach_server.app

# Clean all environments
clean-all:
    @echo "Cleaning all .venv directories..."
    sudo find . -name ".venv" -type d -exec rm -rf {} +
    @echo "✓ All environments cleaned!"

# Install a package to specific project
add project package:
    cd {{project}} && uv add {{package}}

# Remove a package from specific project  
remove project package:
    cd {{project}} && uv remove {{package}}

# Show outdated packages across all projects
outdated:
    @echo "Checking racing-coach-core..."
    cd libs/racing-coach-core && uv tree --outdated || true
    @echo "Checking racing-coach-client..."
    cd apps/racing-coach-client && uv tree --outdated || true
    @echo "Checking racing-coach-server..."
    cd apps/racing-coach-server && uv tree --outdated || true