from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.lap_comparison_response import LapComparisonResponse
from ...types import UNSET, Response


def _get_kwargs(
    *,
    lap_id_1: str,
    lap_id_2: str,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["lap_id_1"] = lap_id_1

    params["lap_id_2"] = lap_id_2

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/metrics/compare",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | LapComparisonResponse | None:
    if response.status_code == 200:
        response_200 = LapComparisonResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | LapComparisonResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    lap_id_1: str,
    lap_id_2: str,
) -> Response[HTTPValidationError | LapComparisonResponse]:
    """Compare Laps

     Compare two laps and return detailed performance deltas.

    This endpoint compares metrics from two laps and returns:
    - Summary statistics (lap time delta, speed deltas, etc.)
    - Per-braking-zone comparisons with matched zones and deltas
    - Per-corner comparisons with matched corners and deltas

    Zones and corners are matched based on distance (closest match within threshold).

    Args:
        lap_id_1 (str): UUID of the baseline lap
        lap_id_2 (str): UUID of the lap to compare against baseline

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | LapComparisonResponse]
    """

    kwargs = _get_kwargs(
        lap_id_1=lap_id_1,
        lap_id_2=lap_id_2,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    lap_id_1: str,
    lap_id_2: str,
) -> HTTPValidationError | LapComparisonResponse | None:
    """Compare Laps

     Compare two laps and return detailed performance deltas.

    This endpoint compares metrics from two laps and returns:
    - Summary statistics (lap time delta, speed deltas, etc.)
    - Per-braking-zone comparisons with matched zones and deltas
    - Per-corner comparisons with matched corners and deltas

    Zones and corners are matched based on distance (closest match within threshold).

    Args:
        lap_id_1 (str): UUID of the baseline lap
        lap_id_2 (str): UUID of the lap to compare against baseline

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | LapComparisonResponse
    """

    return sync_detailed(
        client=client,
        lap_id_1=lap_id_1,
        lap_id_2=lap_id_2,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    lap_id_1: str,
    lap_id_2: str,
) -> Response[HTTPValidationError | LapComparisonResponse]:
    """Compare Laps

     Compare two laps and return detailed performance deltas.

    This endpoint compares metrics from two laps and returns:
    - Summary statistics (lap time delta, speed deltas, etc.)
    - Per-braking-zone comparisons with matched zones and deltas
    - Per-corner comparisons with matched corners and deltas

    Zones and corners are matched based on distance (closest match within threshold).

    Args:
        lap_id_1 (str): UUID of the baseline lap
        lap_id_2 (str): UUID of the lap to compare against baseline

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | LapComparisonResponse]
    """

    kwargs = _get_kwargs(
        lap_id_1=lap_id_1,
        lap_id_2=lap_id_2,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    lap_id_1: str,
    lap_id_2: str,
) -> HTTPValidationError | LapComparisonResponse | None:
    """Compare Laps

     Compare two laps and return detailed performance deltas.

    This endpoint compares metrics from two laps and returns:
    - Summary statistics (lap time delta, speed deltas, etc.)
    - Per-braking-zone comparisons with matched zones and deltas
    - Per-corner comparisons with matched corners and deltas

    Zones and corners are matched based on distance (closest match within threshold).

    Args:
        lap_id_1 (str): UUID of the baseline lap
        lap_id_2 (str): UUID of the lap to compare against baseline

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | LapComparisonResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            lap_id_1=lap_id_1,
            lap_id_2=lap_id_2,
        )
    ).parsed
