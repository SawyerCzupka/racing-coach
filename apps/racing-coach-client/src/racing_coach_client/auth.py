"""Authentication module for the racing-coach-client.

Provides device token authentication using the server's RFC 8628 device authorization flow.
Tokens are stored in a config file at ~/.config/racing-coach/device_token.
"""

import contextlib
import logging
import platform
import sys
import time
import webbrowser
from http import HTTPStatus
from pathlib import Path

from racing_coach_server_client import AuthenticatedClient, Client
from racing_coach_server_client.api.auth import initiate_device_authorization, poll_device_token
from racing_coach_server_client.models import (
    DeviceAuthorizationRequest,
    DeviceAuthorizationResponse,
    DeviceTokenRequest,
    DeviceTokenResponse,
)

logger = logging.getLogger(__name__)

# Config directory for token storage
CONFIG_DIR = Path.home() / ".config" / "racing-coach"
TOKEN_FILE = "device_token"

# Authentication header configuration
DEVICE_TOKEN_HEADER = "X-Device-Token"


class AuthenticationError(Exception):
    """Authentication failed."""


# -----------------------------------------------------------------------------
# Token Storage (file-based)
# -----------------------------------------------------------------------------


def _get_token_path() -> Path:
    """Get the path to the token file."""
    return CONFIG_DIR / TOKEN_FILE


def get_token() -> str | None:
    """Retrieve stored device token from config file."""
    token_path = _get_token_path()
    try:
        if token_path.exists():
            return token_path.read_text().strip()
        return None
    except OSError as e:
        logger.warning(f"Failed to read token file: {e}")
        return None


def store_token(token: str) -> bool:
    """Store device token in config file with secure permissions."""
    token_path = _get_token_path()
    try:
        # Create config directory if needed
        token_path.parent.mkdir(parents=True, exist_ok=True)
        # Write token with restricted permissions (owner read/write only)
        token_path.write_text(token)
        token_path.chmod(0o600)
        logger.info(f"Device token stored in {token_path}")
        return True
    except OSError as e:
        logger.error(f"Failed to store token: {e}")
        return False


def delete_token() -> bool:
    """Delete stored device token."""
    token_path = _get_token_path()
    try:
        if token_path.exists():
            token_path.unlink()
            logger.info("Device token deleted")
        return True
    except OSError as e:
        logger.warning(f"Failed to delete token: {e}")
        return False


# -----------------------------------------------------------------------------
# Device Authorization Flow
# -----------------------------------------------------------------------------


def _get_device_name() -> str:
    """Generate a device name for this machine."""
    hostname = platform.node() or "Unknown"
    return f"Racing Coach Client ({hostname})"


def run_device_auth_flow(base_url: str) -> str:
    """Run the interactive device authorization flow.

    Displays instructions to the user and polls for authorization.

    Args:
        base_url: The server URL.

    Returns:
        The access token.

    Raises:
        AuthenticationError: If authentication fails.
    """
    client = Client(base_url=base_url)

    # Step 1: Initiate device authorization
    print("\n" + "=" * 60)
    print("AUTHENTICATION REQUIRED")
    print("=" * 60)

    device_name = _get_device_name()
    request = DeviceAuthorizationRequest(device_name=device_name)

    response = initiate_device_authorization.sync_detailed(client=client, body=request)

    if response.status_code != HTTPStatus.OK or not isinstance(
        response.parsed, DeviceAuthorizationResponse
    ):
        raise AuthenticationError(f"Failed to initiate device authorization: {response.content}")

    auth_response = response.parsed
    device_code = auth_response.device_code
    user_code = auth_response.user_code
    verification_uri = auth_response.verification_uri
    expires_in = auth_response.expires_in
    interval = auth_response.interval

    # Step 2: Display instructions
    print("\nTo authenticate, please:")
    print(f"  1. Go to: {verification_uri}")
    print(f"  2. Enter code: {user_code}")
    print("\nWaiting for authorization...")
    print("(Press Ctrl+C to cancel)\n")

    # Try to open browser automatically (best-effort)
    with contextlib.suppress(Exception):
        webbrowser.open(verification_uri)

    # Step 3: Poll for token
    poll_request = DeviceTokenRequest(device_code=device_code)
    start_time = time.time()

    while time.time() - start_time < expires_in:
        try:
            poll_response = poll_device_token.sync_detailed(client=client, body=poll_request)

            if poll_response.status_code == HTTPStatus.OK and isinstance(
                poll_response.parsed, DeviceTokenResponse
            ):
                # Success!
                token = poll_response.parsed.access_token
                print("\n" + "=" * 60)
                print("AUTHENTICATION SUCCESSFUL")
                print("=" * 60 + "\n")
                return token

            if poll_response.status_code == HTTPStatus.BAD_REQUEST:
                # Check error type
                try:
                    error_detail = poll_response.parsed
                    if hasattr(error_detail, "detail"):
                        error_info = error_detail.detail  # type: ignore
                        if isinstance(error_info, dict):
                            error_code = error_info.get("error", "")
                            if error_code == "authorization_pending":
                                # Still waiting, continue polling
                                time.sleep(interval)
                                continue
                            elif error_code == "access_denied":
                                raise AuthenticationError("User denied authorization")
                            elif error_code == "expired_token":
                                raise AuthenticationError("Authorization has expired")
                except Exception:
                    pass

                # Unknown 400 error, try parsing from content
                try:
                    import json

                    content = json.loads(poll_response.content)
                    error_code = content.get("detail", {}).get("error", "")
                    if error_code == "authorization_pending":
                        time.sleep(interval)
                        continue
                    elif error_code == "access_denied":
                        raise AuthenticationError("User denied authorization")
                    elif error_code == "expired_token":
                        raise AuthenticationError("Authorization has expired")
                except Exception:
                    pass

            # Wait before next poll
            time.sleep(interval)

        except KeyboardInterrupt:
            print("\nAuthentication cancelled.")
            raise AuthenticationError("Authentication cancelled by user") from None

    raise AuthenticationError("Authorization timed out")


# -----------------------------------------------------------------------------
# Main API
# -----------------------------------------------------------------------------


def get_authenticated_client(base_url: str) -> AuthenticatedClient:
    """Get an authenticated API client.

    If a valid token is stored, uses it. Otherwise, runs the interactive
    device authorization flow.

    Args:
        base_url: The server URL.

    Returns:
        An authenticated client ready for use.

    Raises:
        SystemExit: If authentication fails (exits with code 1).
    """
    # Check for existing token
    token = get_token()

    if token:
        logger.info("Using stored authentication token")
    else:
        # Need to authenticate
        try:
            token = run_device_auth_flow(base_url)
            store_token(token)
        except AuthenticationError as e:
            logger.error(f"Authentication failed: {e}")
            print(f"\nERROR: Authentication failed - {e}")
            print("Please try again or check your server connection.")
            sys.exit(1)

    return AuthenticatedClient(
        base_url=base_url,
        token=token,
        prefix="",  # No prefix, just the raw token
        auth_header_name=DEVICE_TOKEN_HEADER,
    )
