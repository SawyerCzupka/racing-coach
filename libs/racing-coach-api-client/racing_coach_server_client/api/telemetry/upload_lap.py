from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.body_upload_lap import BodyUploadLap
from ...models.http_validation_error import HTTPValidationError
from ...models.lap_upload_response import LapUploadResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: BodyUploadLap,
    lap_id: None | Unset | UUID = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    json_lap_id: None | str | Unset
    if isinstance(lap_id, Unset):
        json_lap_id = UNSET
    elif isinstance(lap_id, UUID):
        json_lap_id = str(lap_id)
    else:
        json_lap_id = lap_id
    params["lap_id"] = json_lap_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/telemetry/lap",
        "params": params,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | LapUploadResponse | None:
    if response.status_code == 200:
        response_200 = LapUploadResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | LapUploadResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: BodyUploadLap,
    lap_id: None | Unset | UUID = UNSET,
) -> Response[HTTPValidationError | LapUploadResponse]:
    """Upload Lap

     Upload a lap with telemetry data.

    Args:
        lap: The lap telemetry data
        session: The session frame with track/car info
        lap_id: Optional client-provided UUID for the lap. If not provided, server generates one.

    The transaction is managed by the transactional_session context manager:
    - If any operation fails, the transaction is automatically rolled back
    - If all operations succeed, changes are committed

    Args:
        lap_id (None | Unset | UUID):
        body (BodyUploadLap):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | LapUploadResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        lap_id=lap_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: BodyUploadLap,
    lap_id: None | Unset | UUID = UNSET,
) -> HTTPValidationError | LapUploadResponse | None:
    """Upload Lap

     Upload a lap with telemetry data.

    Args:
        lap: The lap telemetry data
        session: The session frame with track/car info
        lap_id: Optional client-provided UUID for the lap. If not provided, server generates one.

    The transaction is managed by the transactional_session context manager:
    - If any operation fails, the transaction is automatically rolled back
    - If all operations succeed, changes are committed

    Args:
        lap_id (None | Unset | UUID):
        body (BodyUploadLap):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | LapUploadResponse
    """

    return sync_detailed(
        client=client,
        body=body,
        lap_id=lap_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: BodyUploadLap,
    lap_id: None | Unset | UUID = UNSET,
) -> Response[HTTPValidationError | LapUploadResponse]:
    """Upload Lap

     Upload a lap with telemetry data.

    Args:
        lap: The lap telemetry data
        session: The session frame with track/car info
        lap_id: Optional client-provided UUID for the lap. If not provided, server generates one.

    The transaction is managed by the transactional_session context manager:
    - If any operation fails, the transaction is automatically rolled back
    - If all operations succeed, changes are committed

    Args:
        lap_id (None | Unset | UUID):
        body (BodyUploadLap):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | LapUploadResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        lap_id=lap_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: BodyUploadLap,
    lap_id: None | Unset | UUID = UNSET,
) -> HTTPValidationError | LapUploadResponse | None:
    """Upload Lap

     Upload a lap with telemetry data.

    Args:
        lap: The lap telemetry data
        session: The session frame with track/car info
        lap_id: Optional client-provided UUID for the lap. If not provided, server generates one.

    The transaction is managed by the transactional_session context manager:
    - If any operation fails, the transaction is automatically rolled back
    - If all operations succeed, changes are committed

    Args:
        lap_id (None | Unset | UUID):
        body (BodyUploadLap):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | LapUploadResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            lap_id=lap_id,
        )
    ).parsed
