from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.lap_metrics_response import LapMetricsResponse
from ...types import Response


def _get_kwargs(
    lap_id: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/metrics/lap/{lap_id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | LapMetricsResponse | None:
    if response.status_code == 200:
        response_200 = LapMetricsResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | LapMetricsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    lap_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[HTTPValidationError | LapMetricsResponse]:
    """Get Lap Metrics

     Get metrics for a specific lap.

    Returns all metrics including braking zones and corner analysis.

    Args:
        lap_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | LapMetricsResponse]
    """

    kwargs = _get_kwargs(
        lap_id=lap_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    lap_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> HTTPValidationError | LapMetricsResponse | None:
    """Get Lap Metrics

     Get metrics for a specific lap.

    Returns all metrics including braking zones and corner analysis.

    Args:
        lap_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | LapMetricsResponse
    """

    return sync_detailed(
        lap_id=lap_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    lap_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[HTTPValidationError | LapMetricsResponse]:
    """Get Lap Metrics

     Get metrics for a specific lap.

    Returns all metrics including braking zones and corner analysis.

    Args:
        lap_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | LapMetricsResponse]
    """

    kwargs = _get_kwargs(
        lap_id=lap_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    lap_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> HTTPValidationError | LapMetricsResponse | None:
    """Get Lap Metrics

     Get metrics for a specific lap.

    Returns all metrics including braking zones and corner analysis.

    Args:
        lap_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | LapMetricsResponse
    """

    return (
        await asyncio_detailed(
            lap_id=lap_id,
            client=client,
        )
    ).parsed
