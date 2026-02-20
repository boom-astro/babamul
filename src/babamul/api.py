"""REST API client for Babamul."""

from __future__ import annotations

import base64
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Literal, cast

import httpx
from astropy.coordinates import SkyCoord
from astropy.table import Table

from .config import get_base_url
from .exceptions import APIAuthenticationError, APIError, APINotFoundError
from .models import (
    AlertCutouts,
    CrossMatches,
    LsstAlert,
    ObjectSearchResult,
    ObjPhotometry,
    UserProfile,
    ZtfAlert,
)

logger = logging.getLogger(__name__)

Survey = Literal["ZTF", "LSST"]


def _resolve_token() -> str:
    """Resolve the API token from environment variable.

    Raises
    ------
    APIAuthenticationError
        If no token is found.
    """
    token = os.environ.get("BABAMUL_API_TOKEN")
    if not token:
        raise APIAuthenticationError(
            "No API token provided. Set the BABAMUL_API_TOKEN environment variable.",
            status_code=401,
        )
    return token


def _request(
    method: str,
    endpoint: str,
    *,
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
    url = f"{get_base_url()}{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {_resolve_token()}",
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

    return cast(dict[str, Any], response.json())


def get_alerts(
    survey: Survey,
    *,
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
    is_rock: bool | None = None,
    is_star: bool | None = None,
    is_near_brightstar: bool | None = None,
    is_stationary: bool | None = None,
) -> list[ZtfAlert | LsstAlert]:
    """Query alerts from the API.

    Parameters
    ----------
    survey : Survey
        The survey to query ("ZTF" or "LSST").
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
    is_rock : bool | None
        Filter for likely solar system objects.
    is_star : bool | None
        Filter for likely stellar sources.
    is_near_brightstar : bool | None
        Filter for sources near bright stars.
    is_stationary : bool | None
        Filter for likely stationary sources (not moving).

    Returns
    -------
    list[ZtfAlert | LsstAlert]
        List of alerts matching the query parameters.
    """

    params = {
        key: value
        for key, value in {
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
            "is_rock": is_rock,
            "is_star": is_star,
            "is_near_brightstar": is_near_brightstar,
            "is_stationary": is_stationary,
        }.items()
        if value is not None
    }

    response = _request("GET", f"/surveys/{survey}/alerts", params=params)
    data = response.get("data", [])
    alert_model = ZtfAlert if survey == "ZTF" else LsstAlert
    return [alert_model.model_validate(alert) for alert in data]


def cone_search_alerts(
    survey: Survey,
    coordinates: SkyCoord
    | list[tuple[str, float, float]]
    | list[dict[str, Any]]
    | dict[str, tuple[float, float]]
    | Table,
    radius_arcsec: float,
    *,
    start_jd: float | None = None,
    end_jd: float | None = None,
    min_magpsf: float | None = None,
    max_magpsf: float | None = None,
    min_drb: float | None = None,
    max_drb: float | None = None,
    is_rock: bool | None = None,
    is_star: bool | None = None,
    is_near_brightstar: bool | None = None,
    is_stationary: bool | None = None,
    n_threads: int = 4,
    batch_size: int = 500,
) -> dict[str, list[ZtfAlert | LsstAlert]]:
    """Query alerts from the API.

    Parameters
    ----------
    survey : Survey
        The survey to query ("ZTF" or "LSST").
    coordinates: SkyCoord | list[tuple[str, float, float]] | list[dict[str, Any]]
        Coordinates for the cone search.
    radius_arcsec : float
        Cone search radius in arcseconds (max 600).
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
    is_rock : bool | None
        Filter for likely solar system objects.
    is_star : bool | None
        Filter for likely stellar sources.
    is_near_brightstar : bool | None
        Filter for sources near bright stars.
    is_stationary : bool | None
        Filter for likely stationary sources (not moving).

    Returns
    -------
    list[ZtfAlert | LsstAlert]
        List of alerts matching the query parameters.
    """
    # coordinates can be a SkyCoord (with name), a tuple of (name, ra, dec) or a dict with keys "name", "ra", "dec"
    normalized_coords: dict[str, tuple[float, float]]
    if isinstance(coordinates, SkyCoord):
        if coordinates.isscalar:
            normalized_coords = {
                "coord_0": (
                    float(coordinates.ra.deg),  # type: ignore[union-attr]
                    float(coordinates.dec.deg),  # type: ignore[union-attr]
                )
            }
        else:
            normalized_coords = {
                f"coord_{i}": (float(coord.ra.deg), float(coord.dec.deg))  # type: ignore[union-attr]
                for i, coord in enumerate(coordinates)
            }
    elif isinstance(coordinates, list) and all(
        isinstance(coord, tuple) and len(coord) == 3 for coord in coordinates
    ):
        normalized_coords = {
            name: (float(ra), float(dec)) for name, ra, dec in coordinates
        }
    elif isinstance(coordinates, list) and all(
        isinstance(coord, dict)
        and "name" in coord
        and "ra" in coord
        and "dec" in coord
        for coord in coordinates
    ):
        coord_list = cast(list[dict[str, Any]], coordinates)
        normalized_coords = {
            str(coord["name"]): (float(coord["ra"]), float(coord["dec"]))
            for coord in coord_list
        }
    elif isinstance(coordinates, dict) and all(
        isinstance(coord, tuple) and len(coord) == 2
        for coord in coordinates.values()
    ):
        normalized_coords = {
            k: (float(v[0]), float(v[1])) for k, v in coordinates.items()
        }
    # let's be a little flexible, and allow aliases of "name", "ra", "dec" in the table, as long as we can find them
    elif isinstance(coordinates, Table):
        name_col = next(
            (
                col
                for col in coordinates.colnames
                if col.lower() in ["name", "id", "objname"]
            ),
            None,
        )
        ra_col = next(
            (
                col
                for col in coordinates.colnames
                if col.lower() in ["ra", "ra_deg", "ra_j2000"]
            ),
            None,
        )
        dec_col = next(
            (
                col
                for col in coordinates.colnames
                if col.lower()
                in ["dec", "dec_deg", "dec_j2000", "decl", "declination"]
            ),
            None,
        )
        if name_col and ra_col and dec_col:
            normalized_coords = {
                str(row[name_col]): (float(row[ra_col]), float(row[dec_col]))  # type: ignore[arg-type]
                for row in coordinates
            }
        else:
            raise ValueError(
                "Table must have columns for name, ra, and dec (or their aliases)."
            )
    else:
        raise ValueError(
            "Invalid coordinates format. Must be a SkyCoord, list of (name, ra, dec) tuples, or list of dicts with keys 'name', 'ra', 'dec'."
        )

    if batch_size < 1 or batch_size > 5000:
        raise ValueError("Batch size must be between 1 and 5000.")
    if n_threads < 1 or n_threads > 12:
        raise ValueError("Number of threads must be between 1 and 12.")
    if radius_arcsec <= 0 or radius_arcsec > 600:
        raise ValueError("Radius must be between 0 and 600 arcseconds.")

    # we use the /surveys/{survey}/alerts/cone_search endpoint which accepts a list of coordinates as dicts with keys "name", "ra", "dec"
    params = {
        key: value
        for key, value in {
            "radius_arcsec": radius_arcsec,
            "start_jd": start_jd,
            "end_jd": end_jd,
            "min_magpsf": min_magpsf,
            "max_magpsf": max_magpsf,
            "min_drb": min_drb,
            "max_drb": max_drb,
            "is_rock": is_rock,
            "is_star": is_star,
            "is_near_brightstar": is_near_brightstar,
            "is_stationary": is_stationary,
        }.items()
        if value is not None
    }
    # params["coordinates"] = coordinates
    params["radius_arcsec"] = radius_arcsec

    results = {}
    with ThreadPoolExecutor(max_workers=n_threads) as executor:
        futures = []
        batch = []
        for i, (name, coords) in enumerate(normalized_coords.items()):
            batch.append((name, coords))
            if len(batch) == batch_size or i == len(normalized_coords) - 1:
                batch_coords = dict(batch)
                batch_params: dict[str, Any] = params.copy()
                batch_params["coordinates"] = batch_coords
                futures.append(
                    executor.submit(
                        _request,
                        "POST",
                        f"/surveys/{survey}/alerts/cone_search",
                        json=batch_params,
                    )
                )
                batch = []

        for future in as_completed(futures):
            try:
                response = future.result()
                data = response.get("data", [])
                alert_model = ZtfAlert if survey == "ZTF" else LsstAlert
                for name, alerts in data.items():
                    results[name] = [
                        alert_model.model_validate(alert) for alert in alerts
                    ]
            except Exception as e:
                logger.error(f"Error processing cone search batch: {e}")

    return results


def cone_search_objects(
    survey: Survey,
    coordinates: SkyCoord
    | list[tuple[str, float, float]]
    | list[dict[str, Any]]
    | dict[str, tuple[float, float]]
    | Table,
    radius_arcsec: float,
    n_threads: int = 4,
    batch_size: int = 500,
) -> dict[str, list[ObjectSearchResult]]:
    """Cone search for objects in the API.

    Parameters
    ----------
    survey : Survey
        The survey to query ("ZTF" or "LSST").
    coordinates: SkyCoord | list[tuple[str, float, float]] | list[dict[str, Any]]
        Coordinates for the cone search.
    radius_arcsec : float
        Cone search radius in arcseconds (max 600).

    Returns
    -------
    dict[str, list[ObjectSearchResult]]
        Dictionary mapping coordinate names to lists of matching objects.
    """
    # we can reuse the same coordinate parsing logic as in cone_search_alerts, since the input format is the same
    normalized_coords: dict[str, tuple[float, float]]
    if isinstance(coordinates, SkyCoord):
        if coordinates.isscalar:
            normalized_coords = {
                "coord_0": (
                    float(coordinates.ra.deg),  # type: ignore[union-attr]
                    float(coordinates.dec.deg),  # type: ignore[union-attr]
                )
            }
        else:
            normalized_coords = {
                f"coord_{i}": (float(coord.ra.deg), float(coord.dec.deg))  # type: ignore[union-attr]
                for i, coord in enumerate(coordinates)
            }
    elif isinstance(coordinates, list) and all(
        isinstance(coord, tuple) and len(coord) == 3 for coord in coordinates
    ):
        normalized_coords = {
            name: (float(ra), float(dec)) for name, ra, dec in coordinates
        }
    elif isinstance(coordinates, list) and all(
        isinstance(coord, dict)
        and "name" in coord
        and "ra" in coord
        and "dec" in coord
        for coord in coordinates
    ):
        coord_list = cast(list[dict[str, Any]], coordinates)
        normalized_coords = {
            str(coord["name"]): (float(coord["ra"]), float(coord["dec"]))
            for coord in coord_list
        }
    elif isinstance(coordinates, dict) and all(
        isinstance(coord, tuple) and len(coord) == 2
        for coord in coordinates.values()
    ):
        normalized_coords = {
            k: (float(v[0]), float(v[1])) for k, v in coordinates.items()
        }
    elif isinstance(coordinates, Table):
        name_col = next(
            (
                col
                for col in coordinates.colnames
                if col.lower() in ["name", "id", "objname"]
            ),
            None,
        )
        ra_col = next(
            (
                col
                for col in coordinates.colnames
                if col.lower() in ["ra", "ra_deg", "ra_j2000"]
            ),
            None,
        )
        dec_col = next(
            (
                col
                for col in coordinates.colnames
                if col.lower()
                in ["dec", "dec_deg", "dec_j2000", "decl", "declination"]
            ),
            None,
        )
        if name_col and ra_col and dec_col:
            normalized_coords = {
                str(row[name_col]): (float(row[ra_col]), float(row[dec_col]))  # type: ignore[arg-type]
                for row in coordinates
            }
        else:
            raise ValueError(
                "Table must have columns for name, ra, and dec (or their aliases)."
            )
    else:
        raise ValueError(
            "Invalid coordinates format. Must be a SkyCoord, list of (name, ra, dec) tuples, or list of dicts with keys 'name', 'ra', 'dec'."
        )

    if batch_size < 1 or batch_size > 5000:
        raise ValueError("Batch size must be between 1 and 5000.")
    if n_threads < 1 or n_threads > 12:
        raise ValueError("Number of threads must be between 1 and 12.")
    if radius_arcsec <= 0 or radius_arcsec > 600:
        raise ValueError("Radius must be between 0 and 600 arcseconds.")

    results = {}
    with ThreadPoolExecutor(max_workers=n_threads) as executor:
        futures = []
        batch = []
        for i, (name, coords) in enumerate(normalized_coords.items()):
            batch.append((name, coords))
            if len(batch) == batch_size or i == len(normalized_coords) - 1:
                batch_coords = dict(batch)
                batch_params = {
                    "radius_arcsec": radius_arcsec,
                    "coordinates": batch_coords,
                }
                futures.append(
                    executor.submit(
                        _request,
                        "POST",
                        f"/surveys/{survey}/objects/cone_search",
                        json=batch_params,
                    )
                )
                batch = []

        for future in as_completed(futures):
            try:
                response = future.result()
                data = response.get("data", {})
                for name, objects in data.items():
                    results[name] = [
                        ObjectSearchResult.model_validate(obj)
                        for obj in objects
                    ]
            except Exception as e:
                logger.error(f"Error processing cone search batch: {e}")
    return results


def get_cutouts(survey: Survey, candid: int) -> AlertCutouts:
    """Get cutout images for an alert.

    Parameters
    ----------
    survey : Survey
        Survey ("ZTF" or "LSST").
    candid : int
        Candidate ID of the alert.

    Returns
    -------
    AlertCutouts
        Cutout images (science, template, difference) as bytes.
    """
    response = _request("GET", f"/surveys/{survey}/alerts/{candid}/cutouts")
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


def get_object(survey: Survey, object_id: str) -> ZtfAlert | LsstAlert:
    """Get full object details including history and cutouts.
    This returns the complete object with:
    - Candidate information
    - Full photometry history (prv_candidates, prv_nondetections, fp_hists)
    - Cutout images
    - Cross-matches with other surveys

    Parameters
    ----------
    survey : Survey
        Survey ("ZTF" or "LSST").
    object_id : str
        Object ID.

    Returns
    -------
    ZtfAlert | LsstAlert
        Full object with all available data.
    """
    response = _request("GET", f"/surveys/{survey}/objects/{object_id}")
    data = response.get("data", response)

    for key in ["cutoutScience", "cutoutTemplate", "cutoutDifference"]:
        if data.get(key) and isinstance(data[key], str):
            data[key] = base64.b64decode(data[key])

    if survey == "ZTF":
        return ZtfAlert.model_validate(data)
    elif survey == "LSST":
        return LsstAlert.model_validate(data)
    else:
        raise ValueError(
            f"Survey {survey} is not supported, must be one of: {', '.join(Survey)}"
        )


def get_photometry(survey: Survey, object_id: str) -> ObjPhotometry:
    """Get photometry history for an object.

    Parameters
    ----------
    survey : Survey
        Survey ("ZTF" or "LSST").
    object_id : str
        Object ID.

    Returns
    -------
    dict[str, Photometry]
        Dictionary containing photometry information, including:
        - prv_candidates: list of previous detections
        - prv_nondetections: list of previous non-detections
        - fp_hists: list of forced photometry measurements
    """
    # for now it's just a wrapper around get_object that only returns the photometry, but we can optimize it later if needed
    obj = get_object(survey, object_id)
    return ObjPhotometry(
        objectId=obj.objectId,
        prv_candidates=getattr(obj, "prv_candidates", []),
        prv_nondetections=getattr(obj, "prv_nondetections", []),
        fp_hists=getattr(obj, "fp_hists", []),
    )


def get_cross_matches(survey: Survey, object_id: str) -> CrossMatches:
    """Get cross-matches for an object.

    Parameters
    ----------
    survey : Survey
        Survey ("ZTF" or "LSST").
    object_id : str
        Object ID.

    Returns
    -------
    CrossMatches
        Cross-match information with other archival catalogs (e.g. NED, CatWISE, VSX).
    """
    response = _request("GET", f"/surveys/{survey}/cross_matches/{object_id}")
    data = response.get("data", response)

    return CrossMatches.model_validate(data)


def search_objects(
    object_id: str, limit: int = 10
) -> list[ObjectSearchResult]:
    """Search for objects by partial ID.

    Parameters
    ----------
    object_id : str
        Partial object ID to search for.
    limit : int
        Maximum number of results (1–100, default 10).

    Returns
    -------
    list[ObjectSearchResult]
        List of matching objects with basic info.
    """
    response = _request(
        "GET",
        "/objects",
        params={"object_id": object_id, "limit": min(max(1, limit), 100)},
    )
    data = response.get("data", [])
    return [ObjectSearchResult.model_validate(obj) for obj in data]


def get_profile() -> UserProfile:
    """Get the current user's profile.

    Returns
    -------
    UserProfile
        User profile information.
    """
    response = _request("GET", "/profile")
    data = response.get("data", response)
    return UserProfile.model_validate(data)
