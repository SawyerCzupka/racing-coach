from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.metrics_upload_request import MetricsUploadRequest
from ...models.metrics_upload_response import MetricsUploadResponse
from ...types import Response


def _get_kwargs(
    *,
    body: MetricsUploadRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/metrics/lap",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | MetricsUploadResponse | None:
    if response.status_code == 200:
        response_200 = MetricsUploadResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | MetricsUploadResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: MetricsUploadRequest,
) -> Response[HTTPValidationError | MetricsUploadResponse]:
    """Upload Lap Metrics

     Upload metrics for a lap.

    This endpoint accepts extracted lap metrics and stores them in the database.
    If metrics already exist for the lap, they are replaced (upsert pattern).

    Args:
        body (MetricsUploadRequest): Request model for uploading lap metrics.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | MetricsUploadResponse]
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
    body: MetricsUploadRequest,
) -> HTTPValidationError | MetricsUploadResponse | None:
    """Upload Lap Metrics

     Upload metrics for a lap.

    This endpoint accepts extracted lap metrics and stores them in the database.
    If metrics already exist for the lap, they are replaced (upsert pattern).

    Args:
        body (MetricsUploadRequest): Request model for uploading lap metrics.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | MetricsUploadResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: MetricsUploadRequest,
) -> Response[HTTPValidationError | MetricsUploadResponse]:
    """Upload Lap Metrics

     Upload metrics for a lap.

    This endpoint accepts extracted lap metrics and stores them in the database.
    If metrics already exist for the lap, they are replaced (upsert pattern).

    Args:
        body (MetricsUploadRequest): Request model for uploading lap metrics.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | MetricsUploadResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: MetricsUploadRequest,
) -> HTTPValidationError | MetricsUploadResponse | None:
    """Upload Lap Metrics

     Upload metrics for a lap.

    This endpoint accepts extracted lap metrics and stores them in the database.
    If metrics already exist for the lap, they are replaced (upsert pattern).

    Args:
        body (MetricsUploadRequest): Request model for uploading lap metrics.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | MetricsUploadResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
