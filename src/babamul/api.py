"""A Babamul API client."""

import os
import warnings
from functools import partial
from typing import Literal

import requests
from requests.exceptions import HTTPError


def get_base_url() -> str:
    """Get the API base URL."""
    env = os.getenv("BABAMUL_ENV", "production").lower()
    urls = {
        "local": "http://localhost:4000",
        "production": "https://babamul.caltech.edu/api/babamul",
    }
    return urls[env]


def get_token() -> str | None:
    """Get an API token."""
    token = os.getenv("BABAMUL_TOKEN")
    if token is None:
        warnings.warn("No Babamul token found", stacklevel=1)
    return token


def get_headers(headers: dict | None = None, auth: bool = True) -> dict:
    base_headers = {"Authorization": f"Bearer {get_token()}"} if auth else {}
    if headers is not None:
        return base_headers | headers
    else:
        return base_headers


def _request(
    kind: Literal["get", "post", "put", "patch", "delete"],
    path: str,
    params: dict | None = None,
    json: dict | None = None,
    data: dict | None = None,
    headers: dict | None = None,
    as_json=True,
    auth: bool = True,
    **kwargs,
):
    func = getattr(requests, kind)
    resp = func(
        get_base_url() + path,
        params=params,
        json=json,
        data=data,
        headers=get_headers(headers, auth=auth),
        **kwargs,
    )
    try:
        resp.raise_for_status()
    except HTTPError as e:
        try:
            detail = resp.json()["detail"]
        except Exception:
            raise e from e
        raise HTTPError(f"{resp.status_code}: {detail}") from e
    if as_json:
        return resp.json()
    else:
        return resp


get = partial(_request, "get")
post = partial(_request, "post")
patch = partial(_request, "patch")
put = partial(_request, "put")
delete = partial(_request, "delete")


def get_current_user() -> dict:
    return get("/profile")


def get_alerts(
    survey: Literal["ztf", "lsst"],
    ra: float | None = None,
    dec: float | None = None,
    radius_arcsec: float | None = None,
) -> list[dict]:
    """Get recent alerts from the Babamul API.

    Parameters
    ----------
    survey : {'ztf', 'lsst'}
        The survey to get alerts from.
    ra : float, optional
        Right ascension in degrees.
    dec : float, optional
        Declination in degrees.
    radius_arcsec : float, optional
        Search radius in arcseconds.

    Returns
    -------
    list of dict
        A list of alert dictionaries.
    """
    path = f"/surveys/{survey}/alerts"
    params = {}
    if ra is not None:
        params["ra"] = ra
    if dec is not None:
        params["dec"] = dec
    if radius_arcsec is not None:
        params["radius_arcsec"] = radius_arcsec
    return get(path, params=params)["data"]
