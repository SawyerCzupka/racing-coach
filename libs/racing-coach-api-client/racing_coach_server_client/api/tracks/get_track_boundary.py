from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.track_boundary_response import TrackBoundaryResponse
from ...types import Response


def _get_kwargs(
    boundary_id: UUID,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/tracks/{boundary_id}".format(
            boundary_id=quote(str(boundary_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TrackBoundaryResponse | None:
    if response.status_code == 200:
        response_200 = TrackBoundaryResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | TrackBoundaryResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    boundary_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[HTTPValidationError | TrackBoundaryResponse]:
    """Get Track Boundary

     Get a track boundary by ID.

    Args:
        boundary_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TrackBoundaryResponse]
    """

    kwargs = _get_kwargs(
        boundary_id=boundary_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    boundary_id: UUID,
    *,
    client: AuthenticatedClient,
) -> HTTPValidationError | TrackBoundaryResponse | None:
    """Get Track Boundary

     Get a track boundary by ID.

    Args:
        boundary_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TrackBoundaryResponse
    """

    return sync_detailed(
        boundary_id=boundary_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    boundary_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[HTTPValidationError | TrackBoundaryResponse]:
    """Get Track Boundary

     Get a track boundary by ID.

    Args:
        boundary_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TrackBoundaryResponse]
    """

    kwargs = _get_kwargs(
        boundary_id=boundary_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    boundary_id: UUID,
    *,
    client: AuthenticatedClient,
) -> HTTPValidationError | TrackBoundaryResponse | None:
    """Get Track Boundary

     Get a track boundary by ID.

    Args:
        boundary_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TrackBoundaryResponse
    """

    return (
        await asyncio_detailed(
            boundary_id=boundary_id,
            client=client,
        )
    ).parsed
