# Default recipe - show available commands
default:
    @just --list

# Sync all projects
sync-all:
    @echo "Syncing racing-coach-core..."
    cd libs/racing-coach-core && uv sync
    @echo "Syncing racing-coach-client..."
    cd apps/racing-coach-client && uv sync
    @echo "Syncing racing-coach-server..."
    cd apps/racing-coach-server && uv sync
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
    find . -name ".venv" -type d -exec rm -rf {} +
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