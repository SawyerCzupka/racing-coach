from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.lap_detail_response import LapDetailResponse
from ...types import Response


def _get_kwargs(
    session_id: UUID,
    lap_id: UUID,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/sessions/{session_id}/laps/{lap_id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | LapDetailResponse | None:
    if response.status_code == 200:
        response_200 = LapDetailResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | LapDetailResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    session_id: UUID,
    lap_id: UUID,
    *,
    client: AuthenticatedClient | Client,
) -> Response[HTTPValidationError | LapDetailResponse]:
    """Get Lap

     Get detailed information about a specific lap.

    Args:
        session_id (UUID):
        lap_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | LapDetailResponse]
    """

    kwargs = _get_kwargs(
        session_id=session_id,
        lap_id=lap_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    session_id: UUID,
    lap_id: UUID,
    *,
    client: AuthenticatedClient | Client,
) -> HTTPValidationError | LapDetailResponse | None:
    """Get Lap

     Get detailed information about a specific lap.

    Args:
        session_id (UUID):
        lap_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | LapDetailResponse
    """

    return sync_detailed(
        session_id=session_id,
        lap_id=lap_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    session_id: UUID,
    lap_id: UUID,
    *,
    client: AuthenticatedClient | Client,
) -> Response[HTTPValidationError | LapDetailResponse]:
    """Get Lap

     Get detailed information about a specific lap.

    Args:
        session_id (UUID):
        lap_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | LapDetailResponse]
    """

    kwargs = _get_kwargs(
        session_id=session_id,
        lap_id=lap_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    session_id: UUID,
    lap_id: UUID,
    *,
    client: AuthenticatedClient | Client,
) -> HTTPValidationError | LapDetailResponse | None:
    """Get Lap

     Get detailed information about a specific lap.

    Args:
        session_id (UUID):
        lap_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | LapDetailResponse
    """

    return (
        await asyncio_detailed(
            session_id=session_id,
            lap_id=lap_id,
            client=client,
        )
    ).parsed
