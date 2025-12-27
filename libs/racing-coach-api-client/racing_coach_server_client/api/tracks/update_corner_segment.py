from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.corner_segment_create import CornerSegmentCreate
from ...models.corner_segment_response import CornerSegmentResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    boundary_id: UUID,
    corner_id: UUID,
    *,
    body: CornerSegmentCreate,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/api/v1/tracks/{boundary_id}/corners/{corner_id}".format(
            boundary_id=quote(str(boundary_id), safe=""),
            corner_id=quote(str(corner_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CornerSegmentResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = CornerSegmentResponse.from_dict(response.json())

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
) -> Response[CornerSegmentResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    boundary_id: UUID,
    corner_id: UUID,
    *,
    client: AuthenticatedClient,
    body: CornerSegmentCreate,
) -> Response[CornerSegmentResponse | HTTPValidationError]:
    """Update Corner Segment

     Update a single corner segment's boundaries.

    Args:
        boundary_id (UUID):
        corner_id (UUID):
        body (CornerSegmentCreate): Schema for creating a corner segment.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CornerSegmentResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        boundary_id=boundary_id,
        corner_id=corner_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    boundary_id: UUID,
    corner_id: UUID,
    *,
    client: AuthenticatedClient,
    body: CornerSegmentCreate,
) -> CornerSegmentResponse | HTTPValidationError | None:
    """Update Corner Segment

     Update a single corner segment's boundaries.

    Args:
        boundary_id (UUID):
        corner_id (UUID):
        body (CornerSegmentCreate): Schema for creating a corner segment.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CornerSegmentResponse | HTTPValidationError
    """

    return sync_detailed(
        boundary_id=boundary_id,
        corner_id=corner_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    boundary_id: UUID,
    corner_id: UUID,
    *,
    client: AuthenticatedClient,
    body: CornerSegmentCreate,
) -> Response[CornerSegmentResponse | HTTPValidationError]:
    """Update Corner Segment

     Update a single corner segment's boundaries.

    Args:
        boundary_id (UUID):
        corner_id (UUID):
        body (CornerSegmentCreate): Schema for creating a corner segment.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CornerSegmentResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        boundary_id=boundary_id,
        corner_id=corner_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    boundary_id: UUID,
    corner_id: UUID,
    *,
    client: AuthenticatedClient,
    body: CornerSegmentCreate,
) -> CornerSegmentResponse | HTTPValidationError | None:
    """Update Corner Segment

     Update a single corner segment's boundaries.

    Args:
        boundary_id (UUID):
        corner_id (UUID):
        body (CornerSegmentCreate): Schema for creating a corner segment.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CornerSegmentResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            boundary_id=boundary_id,
            corner_id=corner_id,
            client=client,
            body=body,
        )
    ).parsed
