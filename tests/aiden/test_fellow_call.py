"""Tests for the fellow_call helper that wraps sync Fellow calls."""

from unittest.mock import MagicMock

import pytest

from brew.aiden._fellow_call import NotFoundSpec, fellow_call, fellow_call_or_not_found
from brew.errors import CloudUnreachableError, NotFoundError


async def test_fellow_call_returns_value_on_success() -> None:
    fn = MagicMock(return_value=42)

    result = await fellow_call("compute", fn, 1, 2, mode="x")

    assert result == 42
    fn.assert_called_once_with(1, 2, mode="x")


async def test_fellow_call_wraps_generic_exception_as_cloud_unreachable() -> None:
    fn = MagicMock(side_effect=RuntimeError("boom"))

    with pytest.raises(CloudUnreachableError) as exc_info:
        await fellow_call("do thing", fn)

    err = exc_info.value
    assert err.original == "RuntimeError"
    assert "do thing" in err.message


async def test_fellow_call_or_not_found_returns_value_on_success() -> None:
    fn = MagicMock(return_value="ok")

    result = await fellow_call_or_not_found(
        "fetch",
        NotFoundSpec(resource_kind="profile", resource_id="p0"),
        fn,
    )

    assert result == "ok"


async def test_fellow_call_or_not_found_maps_not_found_string_to_not_found_error() -> None:
    fn = MagicMock(side_effect=Exception("Profile not found"))

    with pytest.raises(NotFoundError) as exc_info:
        await fellow_call_or_not_found(
            "fetch profile",
            NotFoundSpec(resource_kind="profile", resource_id="p0"),
            fn,
        )

    err = exc_info.value
    assert err.resource_kind == "profile"
    assert err.resource_id == "p0"
    assert "p0" in err.message


async def test_fellow_call_or_not_found_falls_through_to_cloud_unreachable() -> None:
    fn = MagicMock(side_effect=RuntimeError("connection timeout"))

    with pytest.raises(CloudUnreachableError) as exc_info:
        await fellow_call_or_not_found(
            "fetch profile",
            NotFoundSpec(resource_kind="profile", resource_id="p0"),
            fn,
        )

    assert exc_info.value.original == "RuntimeError"


async def test_fellow_call_or_not_found_passes_args_and_kwargs() -> None:
    fn = MagicMock(return_value=20)

    result = await fellow_call_or_not_found(
        "echo",
        NotFoundSpec(resource_kind="thing", resource_id="x"),
        fn,
        4,
        b=5,
    )

    assert result == 20
    fn.assert_called_once_with(4, b=5)
