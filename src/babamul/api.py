"""REST API client for Babamul."""

from __future__ import annotations

import base64
import logging
from typing import Literal

import httpx

from .config import APIConfig
from .exceptions import APIAuthenticationError, APIError, APINotFoundError
from .models import LsstAlert, ZtfAlert, ZtfApiAlert, LsstApiAlert, AlertCutouts, KafkaCredential, ObjectSearchResult, UserProfile

logger = logging.getLogger(__name__)

Survey = Literal["ztf", "lsst"]


class APIClient:
    """Client for the Babamul REST API.

    This client provides easy access to alerts, cutouts, and object data
    through the Babamul API.
    """

    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        timeout: float = 30.0,
    ):
        """Initialize the API client.

        Parameters
        ----------
        base_url : str | None
            API base URL. Defaults to BABAMUL_API_URL env var or babamul.caltech.edu.
        token : str | None
            JWT authentication token. Can be set later via login().
        timeout : float
            Request timeout in seconds.
        """
        config = APIConfig.from_env(
            base_url=base_url, token=token, timeout=timeout
        )
        self._base_url = config.base_url
        self._timeout = config.timeout
        self._token = config.token
        self._client = httpx.Client(timeout=self._timeout)

    def __enter__(self) -> APIClient:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    @property
    def is_authenticated(self) -> bool:
        """Check if the client has an authentication token."""
        return self._token is not None

    def _headers(self) -> dict[str, str]:
        """Get request headers with authentication."""
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
        data: dict | None = None,
        require_auth: bool = True,
    ) -> dict:
        """Make an HTTP request to the API.

        Parameters
        ----------
        method : str
            HTTP method (GET, POST, DELETE, etc.)
        endpoint : str
            API endpoint path.
        params : dict | None
            Query parameters.
        json : dict | None
            JSON body for POST requests.
        data : dict | None
            Form data for POST requests.
        require_auth : bool
            Whether authentication is required.

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
        if require_auth and not self._token:
            raise APIAuthenticationError(
                "Authentication required. Call login() first.", status_code=401
            )

        url = f"{self._base_url}{endpoint}"
        headers = self._headers()

        if data is not None:
            headers["Content-Type"] = "application/x-www-form-urlencoded"

        try:
            response = self._client.request(
                method,
                url,
                params=params,
                json=json,
                data=data,
                headers=headers,
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

    # Authentication methods

    def signup(self, email: str) -> dict:
        """Sign up for a new Babamul account.

        An activation code will be sent to the provided email address.

        Parameters
        ----------
        email : str
            Email address for the new account.

        Returns
        -------
        dict
            Response containing signup status.
        """
        return self._request(
            "POST",
            "/signup",
            json={"email": email},
            require_auth=False,
        )

    def activate(self, email: str, activation_code: str) -> dict:
        """Activate a Babamul account.

        Parameters
        ----------
        email : str
            Email address used during signup.
        activation_code : str
            Activation code received via email.

        Returns
        -------
        dict
            Response containing the generated password (shown only once!).
        """
        return self._request(
            "POST",
            "/activate",
            json={"email": email, "activation_code": activation_code},
            require_auth=False,
        )

    def login(self, email: str, password: str) -> str:
        """Authenticate and obtain a JWT token.

        Parameters
        ----------
        email : str
            Account email address.
        password : str
            Account password.

        Returns
        -------
        str
            JWT access token (also stored in the client).
        """
        response = self._request(
            "POST",
            "/auth",
            data={"email": email, "password": password},
            require_auth=False,
        )
        self._token = response.get("access_token")
        if not self._token:
            raise APIAuthenticationError(
                "Login failed: no access token in response",
                status_code=401,
            )
        logger.info("Successfully authenticated with Babamul API")
        return self._token

    def get_profile(self) -> UserProfile:
        """Get the current user's profile.

        Returns
        -------
        UserProfile
            User profile information.
        """
        response = self._request("GET", "/profile")
        data = response.get("data", response)
        return UserProfile(
            id=data.get("_id", data.get("id", "")),
            username=data["username"],
            email=data["email"],
            created_at=data["created_at"],
        )

    # Kafka credentials management

    def create_kafka_credential(self, name: str) -> KafkaCredential:
        """Create a new Kafka credential for stream access.

        Parameters
        ----------
        name : str
            Name for the credential.

        Returns
        -------
        KafkaCredential
            The created credential with username and password.
        """
        response = self._request(
            "POST",
            "/kafka-credentials",
            json={"name": name},
        )
        cred = response.get("credential", response.get("data", response))
        return KafkaCredential(
            id=cred["id"],
            name=cred["name"],
            kafka_username=cred["kafka_username"],
            kafka_password=cred.get("kafka_password"),
            created_at=cred["created_at"],
        )

    def list_kafka_credentials(self) -> list[KafkaCredential]:
        """List all Kafka credentials for the current user.

        Returns
        -------
        list[KafkaCredential]
            List of Kafka credentials.
        """
        response = self._request("GET", "/kafka-credentials")
        data = response.get("data", response)
        if isinstance(data, list):
            return [
                KafkaCredential(
                    id=c["id"],
                    name=c["name"],
                    kafka_username=c["kafka_username"],
                    kafka_password=c.get("kafka_password"),
                    created_at=c["created_at"],
                )
                for c in data
            ]
        return []

    def delete_kafka_credential(self, credential_id: str) -> bool:
        """Delete a Kafka credential.

        Parameters
        ----------
        credential_id : str
            ID of the credential to delete.

        Returns
        -------
        bool
            True if deletion was successful.
        """
        response = self._request(
            "DELETE",
            f"/kafka-credentials/{credential_id}",
        )
        return response.get("deleted", False)

    # Alert methods

    def get_alerts(
        self,
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
    ) -> list[ZtfApiAlert | LsstApiAlert]:
        """Query alerts from the API.

        Parameters
        ----------
        survey : Survey
            The survey to query ("ztf" or "lsst").
        object_id : str | None
            Filter by object ID.
        ra : float | None
            Right Ascension in degrees (requires dec and radius_arcsec).
        dec : float | None
            Declination in degrees (requires ra and radius_arcsec).
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
        list
        """
        if object_id and (ra or dec or radius_arcsec):
            logger.warning("Both object_id and (ra, dec, radius_arcsec) provided; Only object_id will be used.")
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

        response = self._request(
            "GET",
            f"/surveys/{survey}/alerts",
            params=params,
        )
        data = response.get("data", [])
        alert_model = ZtfApiAlert if survey == "ztf" else LsstApiAlert
        return [alert_model.model_validate(alert) for alert in data]

    def get_cutouts(self, survey: Survey, candid: int) -> AlertCutouts:
        """Get cutout images for an alert.

        Parameters
        ----------
        survey : Survey
            Survey ("ztf" or "lsst").
        candid : int
            Candidate ID of the alert.

        Returns
        -------
        AlertCutouts
            Cutout images (science, template, difference) as bytes.
        """
        response = self._request(
            "GET",
            f"/surveys/{survey}/alerts/{candid}/cutouts",
        )

        data = response.get("data", response)
        return AlertCutouts(
            candid=data["candid"],
            cutoutScience=base64.b64decode(data["cutoutScience"])
            if data.get("cutoutScience")
            else None,
            cutoutTemplate=base64.b64decode(data["cutoutTemplate"])
            if data.get("cutoutTemplate")
            else None,
            cutoutDifference=base64.b64decode(data["cutoutDifference"])
            if data.get("cutoutDifference")
            else None,
        )

    def get_object(
        self, survey: Survey, object_id: str
    ) -> ZtfAlert | LsstAlert:
        """Get full object details including history and cutouts.

        This returns the complete object with:
        - Latest candidate information
        - Full photometry history (prv_candidates, prv_nondetections, fp_hists)
        - Cutout images
        - Cross-matches with other surveys

        Parameters
        ----------
        survey : Survey
            Survey ("ztf" or "lsst").
        object_id : str
            Object ID

        Returns
        -------
        ZtfAlert | LsstAlert
            Full object with all available data.
        """
        response = self._request(
            "GET",
            f"/surveys/{survey}/objects/{object_id}",
        )

        data = response.get("data", response)

        # Decode base64 cutouts if present
        for key in ["cutoutScience", "cutoutTemplate", "cutoutDifference"]:
            if data.get(key) and isinstance(data[key], str):
                data[key] = base64.b64decode(data[key])

        if survey == "ztf":
            return ZtfAlert.model_validate(data)
        return LsstAlert.model_validate(data)

    def search_objects(
        self, object_id: str, limit: int = 10
    ) -> list[ObjectSearchResult]:
        """Search for objects by partial ID.

        Parameters
        ----------
        object_id : str
            Partial object ID to search for.
        limit : int
            Maximum number of results (1-100, default 10).

        Returns
        -------
        list[ObjectSearchResult]
            List of matching objects with basic info.
        """
        response = self._request(
            "GET",
            "/objects",
            params={"object_id": object_id, "limit": min(max(1, limit), 100)},
        )

        data = response.get("data", [])
        return [ObjectSearchResult.model_validate(obj) for obj in data]
