from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.body_upload_track_boundary import BodyUploadTrackBoundary
from ...models.http_validation_error import HTTPValidationError
from ...models.track_boundary_upload_response import TrackBoundaryUploadResponse
from ...types import Response


def _get_kwargs(
    *,
    body: BodyUploadTrackBoundary,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/tracks/upload",
    }

    _kwargs["files"] = body.to_multipart()

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TrackBoundaryUploadResponse | None:
    if response.status_code == 200:
        response_200 = TrackBoundaryUploadResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | TrackBoundaryUploadResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: BodyUploadTrackBoundary,
) -> Response[HTTPValidationError | TrackBoundaryUploadResponse]:
    """Upload Track Boundary

     Upload an IBT file to generate and store a track boundary.

    The IBT file should contain at least two laps:
    - One lap hugging the left side of the track
    - One lap hugging the right side of the track

    If a boundary already exists for the track+config, it will be replaced.

    Defaults follow the Garage61 collection method:
    - Left boundary: Lap 1 (after reset at start line)
    - Right boundary: Lap 3 (after reset at start line)

    Args:
        body (BodyUploadTrackBoundary):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TrackBoundaryUploadResponse]
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
    body: BodyUploadTrackBoundary,
) -> HTTPValidationError | TrackBoundaryUploadResponse | None:
    """Upload Track Boundary

     Upload an IBT file to generate and store a track boundary.

    The IBT file should contain at least two laps:
    - One lap hugging the left side of the track
    - One lap hugging the right side of the track

    If a boundary already exists for the track+config, it will be replaced.

    Defaults follow the Garage61 collection method:
    - Left boundary: Lap 1 (after reset at start line)
    - Right boundary: Lap 3 (after reset at start line)

    Args:
        body (BodyUploadTrackBoundary):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TrackBoundaryUploadResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: BodyUploadTrackBoundary,
) -> Response[HTTPValidationError | TrackBoundaryUploadResponse]:
    """Upload Track Boundary

     Upload an IBT file to generate and store a track boundary.

    The IBT file should contain at least two laps:
    - One lap hugging the left side of the track
    - One lap hugging the right side of the track

    If a boundary already exists for the track+config, it will be replaced.

    Defaults follow the Garage61 collection method:
    - Left boundary: Lap 1 (after reset at start line)
    - Right boundary: Lap 3 (after reset at start line)

    Args:
        body (BodyUploadTrackBoundary):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TrackBoundaryUploadResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: BodyUploadTrackBoundary,
) -> HTTPValidationError | TrackBoundaryUploadResponse | None:
    """Upload Track Boundary

     Upload an IBT file to generate and store a track boundary.

    The IBT file should contain at least two laps:
    - One lap hugging the left side of the track
    - One lap hugging the right side of the track

    If a boundary already exists for the track+config, it will be replaced.

    Defaults follow the Garage61 collection method:
    - Left boundary: Lap 1 (after reset at start line)
    - Right boundary: Lap 3 (after reset at start line)

    Args:
        body (BodyUploadTrackBoundary):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TrackBoundaryUploadResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
