from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.authorize_device_request import AuthorizeDeviceRequest
from ...models.confirm_device_authorization_response_confirmdeviceauthorization import (
    ConfirmDeviceAuthorizationResponseConfirmdeviceauthorization,
)
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    *,
    body: AuthorizeDeviceRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/auth/device/confirm",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ConfirmDeviceAuthorizationResponseConfirmdeviceauthorization | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = ConfirmDeviceAuthorizationResponseConfirmdeviceauthorization.from_dict(response.json())

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
) -> Response[ConfirmDeviceAuthorizationResponseConfirmdeviceauthorization | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: AuthorizeDeviceRequest,
) -> Response[ConfirmDeviceAuthorizationResponseConfirmdeviceauthorization | HTTPValidationError]:
    """Authorize Device From Web

     Authorize a device from web UI.

    User enters the user_code shown on their desktop client.
    This endpoint requires authentication (user must be logged in via web).

    Args:
        body (AuthorizeDeviceRequest): Request model for authorizing a device (from web UI).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ConfirmDeviceAuthorizationResponseConfirmdeviceauthorization | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    body: AuthorizeDeviceRequest,
) -> ConfirmDeviceAuthorizationResponseConfirmdeviceauthorization | HTTPValidationError | None:
    """Authorize Device From Web

     Authorize a device from web UI.

    User enters the user_code shown on their desktop client.
    This endpoint requires authentication (user must be logged in via web).

    Args:
        body (AuthorizeDeviceRequest): Request model for authorizing a device (from web UI).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ConfirmDeviceAuthorizationResponseConfirmdeviceauthorization | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: AuthorizeDeviceRequest,
) -> Response[ConfirmDeviceAuthorizationResponseConfirmdeviceauthorization | HTTPValidationError]:
    """Authorize Device From Web

     Authorize a device from web UI.

    User enters the user_code shown on their desktop client.
    This endpoint requires authentication (user must be logged in via web).

    Args:
        body (AuthorizeDeviceRequest): Request model for authorizing a device (from web UI).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ConfirmDeviceAuthorizationResponseConfirmdeviceauthorization | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: AuthorizeDeviceRequest,
) -> ConfirmDeviceAuthorizationResponseConfirmdeviceauthorization | HTTPValidationError | None:
    """Authorize Device From Web

     Authorize a device from web UI.

    User enters the user_code shown on their desktop client.
    This endpoint requires authentication (user must be logged in via web).

    Args:
        body (AuthorizeDeviceRequest): Request model for authorizing a device (from web UI).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ConfirmDeviceAuthorizationResponseConfirmdeviceauthorization | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
