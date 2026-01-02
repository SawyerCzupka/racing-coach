from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.device_authorization_request import DeviceAuthorizationRequest
from ...models.device_authorization_response import DeviceAuthorizationResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    *,
    body: DeviceAuthorizationRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/auth/device/authorize",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DeviceAuthorizationResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = DeviceAuthorizationResponse.from_dict(response.json())

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
) -> Response[DeviceAuthorizationResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: DeviceAuthorizationRequest,
) -> Response[DeviceAuthorizationResponse | HTTPValidationError]:
    """Initiate Device Authorization

     Initiate OAuth device authorization flow.

    Called by desktop client to get device_code and user_code.
    The user_code should be displayed to the user who then enters it
    at the verification_uri in their browser.

    Args:
        body (DeviceAuthorizationRequest): Request model for initiating device authorization.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeviceAuthorizationResponse | HTTPValidationError]
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
    client: AuthenticatedClient | Client,
    body: DeviceAuthorizationRequest,
) -> DeviceAuthorizationResponse | HTTPValidationError | None:
    """Initiate Device Authorization

     Initiate OAuth device authorization flow.

    Called by desktop client to get device_code and user_code.
    The user_code should be displayed to the user who then enters it
    at the verification_uri in their browser.

    Args:
        body (DeviceAuthorizationRequest): Request model for initiating device authorization.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeviceAuthorizationResponse | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: DeviceAuthorizationRequest,
) -> Response[DeviceAuthorizationResponse | HTTPValidationError]:
    """Initiate Device Authorization

     Initiate OAuth device authorization flow.

    Called by desktop client to get device_code and user_code.
    The user_code should be displayed to the user who then enters it
    at the verification_uri in their browser.

    Args:
        body (DeviceAuthorizationRequest): Request model for initiating device authorization.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeviceAuthorizationResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: DeviceAuthorizationRequest,
) -> DeviceAuthorizationResponse | HTTPValidationError | None:
    """Initiate Device Authorization

     Initiate OAuth device authorization flow.

    Called by desktop client to get device_code and user_code.
    The user_code should be displayed to the user who then enters it
    at the verification_uri in their browser.

    Args:
        body (DeviceAuthorizationRequest): Request model for initiating device authorization.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeviceAuthorizationResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
