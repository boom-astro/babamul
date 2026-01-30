"""REST API client for Babamul."""

from __future__ import annotations

import base64
import logging
from typing import Literal

import httpx
from pydantic import BaseModel

from .config import APIConfig
from .exceptions import APIAuthenticationError, APIError, APINotFoundError
from .models import BabamulLsstAlert, BabamulZtfAlert

logger = logging.getLogger(__name__)

Survey = Literal["ztf", "lsst"]


class AlertCutouts(BaseModel):
    """Cutout images for an alert."""

    candid: int
    cutoutScience: bytes | None = None
    cutoutTemplate: bytes | None = None
    cutoutDifference: bytes | None = None

    model_config = {"arbitrary_types_allowed": True}


class ObjectSearchResult(BaseModel):
    """Result from object search."""

    objectId: str
    ra: float
    dec: float
    survey: str


class KafkaCredential(BaseModel):
    """Kafka credential information."""

    id: str
    name: str
    kafka_username: str
    kafka_password: str | None = None
    created_at: int


class UserProfile(BaseModel):
    """User profile information."""

    id: str
    username: str
    email: str
    created_at: int


class APIClient:
    """Client for the Babamul REST API.

    This client provides easy access to alerts, cutouts, and object data
    through the Babamul API.

    Examples
    --------
    Basic usage with email/password authentication:

    >>> client = APIClient()
    >>> client.login("user@example.com", "password")
    >>> alerts = client.get_alerts("ztf", object_id="ZTF20aaxxxx")
    >>> for alert in alerts:
    ...     cutouts = client.get_cutouts("ztf", alert.candid)
    ...     # cutouts.cutoutScience, cutouts.cutoutTemplate, etc.

    Using with an alert from Kafka:

    >>> from babamul import AlertConsumer, APIClient
    >>> client = APIClient()
    >>> client.login("user@example.com", "password")
    >>> for alert in AlertConsumer(topics=["babamul.ztf.lsst-match.hosted"]):
    ...     # Get fresh cutouts from API for this alert
    ...     cutouts = client.get_cutouts_for_alert(alert)

    Getting a full object with all history:

    >>> obj = client.get_object("ztf", "ZTF20aaxxxx")
    >>> obj.get_photometry()  # Full light curve
    >>> obj.show_cutouts()    # Display cutout images
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
            print(response.text)
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
            "/babamul/signup",
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
            "/babamul/activate",
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
            "/babamul/auth",
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
        response = self._request("GET", "/babamul/profile")
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
            "/babamul/kafka-credentials",
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
        response = self._request("GET", "/babamul/kafka-credentials")
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
            f"/babamul/kafka-credentials/{credential_id}",
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
    ) -> list[BabamulZtfAlert] | list[BabamulLsstAlert]:
        """Query alerts from the API.

        Parameters
        ----------
        survey : Survey
            Survey to query ("ztf" or "lsst").
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
        list[BabamulZtfAlert] | list[BabamulLsstAlert]
            List of alerts matching the query.
        """
        params: dict = {}
        if object_id:
            params["object_id"] = object_id
        if ra is not None:
            params["ra"] = ra
        if dec is not None:
            params["dec"] = dec
        if radius_arcsec is not None:
            params["radius_arcsec"] = radius_arcsec
        if start_jd is not None:
            params["start_jd"] = start_jd
        if end_jd is not None:
            params["end_jd"] = end_jd
        if min_magpsf is not None:
            params["min_magpsf"] = min_magpsf
        if max_magpsf is not None:
            params["max_magpsf"] = max_magpsf
        if min_drb is not None:
            params["min_drb"] = min_drb
        if max_drb is not None:
            params["max_drb"] = max_drb

        response = self._request(
            "GET",
            f"/babamul/surveys/{survey}/alerts",
            params=params or None,
        )

        data = response.get("data", [])
        if survey == "ztf":
            return [BabamulZtfAlert.model_validate(alert) for alert in data]
        return [BabamulLsstAlert.model_validate(alert) for alert in data]

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
            f"/babamul/surveys/{survey}/alerts/{candid}/cutouts",
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

    def get_cutouts_for_alert(
        self, alert: BabamulZtfAlert | BabamulLsstAlert
    ) -> AlertCutouts:
        """Get cutout images for a Babamul alert object.

        This is a convenience method to easily fetch cutouts for an alert
        received from the Kafka stream.

        Parameters
        ----------
        alert : BabamulZtfAlert | BabamulLsstAlert
            Alert object from Kafka consumer or API.

        Returns
        -------
        AlertCutouts
            Cutout images (science, template, difference) as bytes.

        Examples
        --------
        >>> from babamul import AlertConsumer, APIClient
        >>> client = APIClient()
        >>> client.login("user@example.com", "password")
        >>> for alert in AlertConsumer(topics=["babamul.ztf.lsst-match.hosted"]):
        ...     cutouts = client.get_cutouts_for_alert(alert)
        ...     # Process cutouts...
        """
        survey: Survey = "ztf" if alert.survey == "ZTF" else "lsst"
        return self.get_cutouts(survey, alert.candid)

    def get_object(
        self, survey: Survey, object_id: str
    ) -> BabamulZtfAlert | BabamulLsstAlert:
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
            Object ID (e.g., "ZTF20aaxxxx" or "LSST123456789").

        Returns
        -------
        BabamulZtfAlert | BabamulLsstAlert
            Full object with all available data.

        Examples
        --------
        >>> obj = client.get_object("ztf", "ZTF20aaxxxx")
        >>> phot = obj.get_photometry()
        >>> obj.show_cutouts()
        """
        response = self._request(
            "GET",
            f"/babamul/surveys/{survey}/objects/{object_id}",
        )

        data = response.get("data", response)

        # Decode base64 cutouts if present
        for key in ["cutoutScience", "cutoutTemplate", "cutoutDifference"]:
            if data.get(key) and isinstance(data[key], str):
                data[key] = base64.b64decode(data[key])

        if survey == "ztf":
            return BabamulZtfAlert.model_validate(data)
        return BabamulLsstAlert.model_validate(data)

    def get_object_for_alert(
        self, alert: BabamulZtfAlert | BabamulLsstAlert
    ) -> BabamulZtfAlert | BabamulLsstAlert:
        """Get full object details for a Babamul alert.

        This is useful when you have an alert from Kafka and want to fetch
        the complete object history from the API.

        Parameters
        ----------
        alert : BabamulZtfAlert | BabamulLsstAlert
            Alert object from Kafka consumer.

        Returns
        -------
        BabamulZtfAlert | BabamulLsstAlert
            Full object with all available data.

        Examples
        --------
        >>> for alert in AlertConsumer(topics=["babamul.ztf.lsst-match.hosted"]):
        ...     # Get full object with complete history
        ...     full_obj = client.get_object_for_alert(alert)
        ...     print(f"Full light curve has {len(full_obj.get_photometry())} points")
        """
        survey: Survey = "ztf" if alert.survey == "ZTF" else "lsst"
        return self.get_object(survey, alert.objectId)

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
            "/babamul/objects",
            params={"object_id": object_id, "limit": min(max(1, limit), 100)},
        )

        data = response.get("data", [])
        return [ObjectSearchResult.model_validate(obj) for obj in data]

    def cone_search(
        self,
        survey: Survey,
        ra: float,
        dec: float,
        radius_arcsec: float,
        **kwargs,
    ) -> list[BabamulZtfAlert] | list[BabamulLsstAlert]:
        """Search for alerts within a cone around a position.

        Parameters
        ----------
        survey : Survey
            Survey to search ("ztf" or "lsst").
        ra : float
            Right Ascension in degrees.
        dec : float
            Declination in degrees.
        radius_arcsec : float
            Search radius in arcseconds (max 600).
        **kwargs
            Additional filters (start_jd, end_jd, min_magpsf, etc.).

        Returns
        -------
        list[BabamulZtfAlert] | list[BabamulLsstAlert]
            Alerts within the search cone.

        Examples
        --------
        >>> alerts = client.cone_search("ztf", ra=180.0, dec=45.0, radius_arcsec=60)
        """
        return self.get_alerts(
            survey, ra=ra, dec=dec, radius_arcsec=radius_arcsec, **kwargs
        )
