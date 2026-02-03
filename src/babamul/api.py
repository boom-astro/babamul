"""REST API client for Babamul."""

from __future__ import annotations

import os
import base64
import logging
from typing import Any, Literal

import httpx

from .config import get_base_url
from .exceptions import APIAuthenticationError, APIError, APINotFoundError
from .models import (
    AlertCutouts,
    LsstAlert,
    LsstApiAlert,
    ObjectSearchResult,
    UserProfile,
    ZtfAlert,
    ZtfApiAlert,
)

logger = logging.getLogger(__name__)

Survey = Literal["ztf", "lsst"]


def _resolve_token(token: str | None = None) -> str:
    """Return *token* if given, else fall back to ``BABAMUL_API_TOKEN`` env var.

    Raises
    ------
    APIAuthenticationError
        If neither source provides a token.
    """
    resolved = token or os.environ.get("BABAMUL_API_TOKEN")
    if not resolved:
        raise APIAuthenticationError(
            "No API token provided. Pass token= or set BABAMUL_API_TOKEN.",
            status_code=401,
        )
    return resolved


def _request(
    method: str,
    endpoint: str,
    *,
    token: str | None = None,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Make an authenticated HTTP request to the Babamul API.

    Parameters
    ----------
    method : str
        HTTP method (GET, POST, DELETE, …).
    endpoint : str
        API endpoint path (e.g. ``/profile``).
    token : str | None
        Bearer token.  Resolved via :func:`_resolve_token`.
    params : dict | None
        Query parameters.
    json : dict | None
        JSON body for POST requests.

    Returns
    -------
    dict
        Response JSON data.

    Raises
    ------
    APIAuthenticationError
        If authentication is required but no token is set, or auth fails.
    APINotFoundError
        If the requested resource is not found.
    APIError
        For other API errors.
    """
    resolved_token = _resolve_token(token)
    url = f"{get_base_url()}{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {resolved_token}",
    }

    try:
        response = httpx.request(
            method,
            url,
            params=params,
            json=json,
            headers=headers,
            timeout=30.0,
        )
    except httpx.RequestError as e:
        raise APIError(f"Request failed: {e}") from e

    if response.status_code == 401:
        raise APIAuthenticationError(
            "Authentication failed. Check your credentials.",
            status_code=401,
        )
    if response.status_code == 404:
        raise APINotFoundError(
            f"Resource not found: {endpoint}",
            status_code=404,
        )
    if response.status_code >= 400:
        try:
            error_data = response.json()
            message = error_data.get("message", response.text)
        except Exception:
            message = response.text
        raise APIError(
            f"API error ({response.status_code}): {message}",
            status_code=response.status_code,
        )

    return response.json()


def get_alerts(
    survey: Survey,
    *,
    token: str | None = None,
    object_id: str | None = None,
    ra: float | None = None,
    dec: float | None = None,
    radius_arcsec: float | None = None,
    start_jd: float | None = None,
    end_jd: float | None = None,
    min_magpsf: float | None = None,
    max_magpsf: float | None = None,
    min_drb: float | None = None,
    max_drb: float | None = None,
) -> list[ZtfApiAlert | LsstApiAlert]:
    """Query alerts from the API.

    Parameters
    ----------
    survey : Survey
        The survey to query ("ztf" or "lsst").
    token : str | None
        Bearer token (falls back to ``BABAMUL_API_TOKEN``).
    object_id : str | None
        Filter by object ID.
    ra : float | None
        Right Ascension in degrees (requires *dec* and *radius_arcsec*).
    dec : float | None
        Declination in degrees (requires *ra* and *radius_arcsec*).
    radius_arcsec : float | None
        Cone search radius in arcseconds (max 600).
    start_jd : float | None
        Start Julian Date filter.
    end_jd : float | None
        End Julian Date filter.
    min_magpsf : float | None
        Minimum PSF magnitude filter.
    max_magpsf : float | None
        Maximum PSF magnitude filter.
    min_drb : float | None
        Minimum DRB (reliability) score filter.
    max_drb : float | None
        Maximum DRB score filter.

    Returns
    -------
    list[ZtfApiAlert | LsstApiAlert]
        List of alerts matching the query parameters.
    """
    if object_id and (ra is not None or dec is not None or radius_arcsec is not None):
        logger.warning(
            "Both object_id and (ra, dec, radius_arcsec) provided; "
            "Only object_id will be used."
        )
    elif not object_id and (ra is None or dec is None or radius_arcsec is None):
        raise ValueError(
            "Either object_id or (ra, dec, radius_arcsec) must be provided"
        )

    params = {
        key: value for key, value in {
            "object_id": object_id,
            "ra": ra,
            "dec": dec,
            "radius_arcsec": radius_arcsec,
            "start_jd": start_jd,
            "end_jd": end_jd,
            "min_magpsf": min_magpsf,
            "max_magpsf": max_magpsf,
            "min_drb": min_drb,
            "max_drb": max_drb,
        }.items() if value is not None
    }

    response = _request("GET", f"/surveys/{survey}/alerts", token=token, params=params)
    data = response.get("data", [])
    alert_model = ZtfApiAlert if survey == "ztf" else LsstApiAlert
    return [alert_model.model_validate(alert) for alert in data]


def get_cutouts(survey: Survey, candid: int, *, token: str | None = None) -> AlertCutouts:
    """Get cutout images for an alert.

    Parameters
    ----------
    survey : Survey
        Survey ("ztf" or "lsst").
    candid : int
        Candidate ID of the alert.
    token : str | None
        Bearer token (falls back to ``BABAMUL_API_TOKEN``).

    Returns
    -------
    AlertCutouts
        Cutout images (science, template, difference) as bytes.
    """
    response = _request(
        "GET", f"/surveys/{survey}/alerts/{candid}/cutouts", token=token
    )
    data = response.get("data", response)
    return AlertCutouts(
        candid=data["candid"],
        cutoutScience=base64.b64decode(data["cutoutScience"])
        if data.get("cutoutScience")
        else b"",
        cutoutTemplate=base64.b64decode(data["cutoutTemplate"])
        if data.get("cutoutTemplate")
        else b"",
        cutoutDifference=base64.b64decode(data["cutoutDifference"])
        if data.get("cutoutDifference")
        else b"",
    )


def get_object(
    survey: Survey, object_id: str, *, token: str | None = None
) -> ZtfAlert | LsstAlert:
    """Get full object details including history and cutouts.
    This returns the complete object with:
    - Candidate information
    - Full photometry history (prv_candidates, prv_nondetections, fp_hists)
    - Cutout images
    - Cross-matches with other surveys

    Parameters
    ----------
    survey : Survey
        Survey ("ztf" or "lsst").
    object_id : str
        Object ID.
    token : str | None
        Bearer token (falls back to ``BABAMUL_API_TOKEN``).

    Returns
    -------
    ZtfAlert | LsstAlert
        Full object with all available data.
    """
    response = _request(
        "GET", f"/surveys/{survey}/objects/{object_id}", token=token
    )
    data = response.get("data", response)

    for key in ["cutoutScience", "cutoutTemplate", "cutoutDifference"]:
        if data.get(key) and isinstance(data[key], str):
            data[key] = base64.b64decode(data[key])

    if survey == "ztf":
        return ZtfAlert.model_validate(data)
    return LsstAlert.model_validate(data)


def search_objects(
    object_id: str, limit: int = 10, *, token: str | None = None
) -> list[ObjectSearchResult]:
    """Search for objects by partial ID.

    Parameters
    ----------
    object_id : str
        Partial object ID to search for.
    limit : int
        Maximum number of results (1–100, default 10).
    token : str | None
        Bearer token (falls back to ``BABAMUL_API_TOKEN``).

    Returns
    -------
    list[ObjectSearchResult]
        List of matching objects with basic info.
    """
    response = _request(
        "GET",
        "/objects",
        token=token,
        params={"object_id": object_id, "limit": min(max(1, limit), 100)},
    )
    data = response.get("data", [])
    return [ObjectSearchResult.model_validate(obj) for obj in data]


def get_profile(*, token: str | None = None) -> UserProfile:
    """Get the current user's profile.

    Parameters
    ----------
    token : str | None
        Bearer token (falls back to ``BABAMUL_API_TOKEN``).

    Returns
    -------
    UserProfile
        User profile information.
    """
    response = _request("GET", "/profile", token=token)
    data = response.get("data", response)
    return UserProfile.model_validate(data)
