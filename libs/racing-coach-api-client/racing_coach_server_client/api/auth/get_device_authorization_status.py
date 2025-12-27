from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.device_authorization_status import DeviceAuthorizationStatus
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    user_code: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/auth/device/status/{user_code}".format(
            user_code=quote(str(user_code), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DeviceAuthorizationStatus | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = DeviceAuthorizationStatus.from_dict(response.json())

        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[DeviceAuthorizationStatus | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    user_code: str,
    *,
    client: AuthenticatedClient,
) -> Response[DeviceAuthorizationStatus | HTTPValidationError]:
    """Get Device Authorization Status

     Get the status of a device authorization.

    Used by the web UI to show device details before confirming.

    Args:
        user_code (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeviceAuthorizationStatus | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        user_code=user_code,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    user_code: str,
    *,
    client: AuthenticatedClient,
) -> DeviceAuthorizationStatus | HTTPValidationError | None:
    """Get Device Authorization Status

     Get the status of a device authorization.

    Used by the web UI to show device details before confirming.

    Args:
        user_code (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeviceAuthorizationStatus | HTTPValidationError
    """

    return sync_detailed(
        user_code=user_code,
        client=client,
    ).parsed


async def asyncio_detailed(
    user_code: str,
    *,
    client: AuthenticatedClient,
) -> Response[DeviceAuthorizationStatus | HTTPValidationError]:
    """Get Device Authorization Status

     Get the status of a device authorization.

    Used by the web UI to show device details before confirming.

    Args:
        user_code (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeviceAuthorizationStatus | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        user_code=user_code,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    user_code: str,
    *,
    client: AuthenticatedClient,
) -> DeviceAuthorizationStatus | HTTPValidationError | None:
    """Get Device Authorization Status

     Get the status of a device authorization.

    Used by the web UI to show device details before confirming.

    Args:
        user_code (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeviceAuthorizationStatus | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            user_code=user_code,
            client=client,
        )
    ).parsed
