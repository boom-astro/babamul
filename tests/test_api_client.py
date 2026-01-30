"""Tests for babamul.api_client against a real API at localhost:4000."""

import pytest

from babamul import APIClient
from babamul.api_client import (
    AlertCutouts,
    KafkaCredential,
    ObjectSearchResult,
    UserProfile,
)
from babamul.exceptions import (
    APIAuthenticationError,
    APIError,
    APINotFoundError,
)
from babamul.models import BabamulLsstAlert, BabamulZtfAlert

BASE_URL = "BASE_URL"
EMAIL = "EMAIL"
PASSWORD = "PASSWORD"


# ---- Fixtures ----


@pytest.fixture(scope="session")
def authed_client():
    """Session-scoped authenticated APIClient."""
    client = APIClient(base_url=BASE_URL)
    client.login(EMAIL, PASSWORD)
    yield client
    client.close()


@pytest.fixture
def client():
    """Unauthenticated APIClient."""
    c = APIClient(base_url=BASE_URL)
    yield c
    c.close()


# ---- Initialization tests ----


class TestAPIClientInit:
    def test_context_manager(self):
        with APIClient(base_url=BASE_URL) as c:
            assert not c.is_authenticated

    def test_no_token_by_default(self, client):
        assert not client.is_authenticated

    def test_base_url_stored(self, client):
        assert client._base_url == BASE_URL

    def test_requires_auth_without_token(self, client):
        with pytest.raises(
            APIAuthenticationError, match="Authentication required"
        ):
            client._request("GET", "/babamul/profile")


# ---- Auth tests ----


class TestAPIClientAuth:
    def test_login_bad_credentials(self, client):
        with pytest.raises((APIAuthenticationError, APIError)):
            client.login("nonexistent@example.com", "wrongpassword")

    def test_login_success(self):
        with APIClient(base_url=BASE_URL) as c:
            token = c.login(EMAIL, PASSWORD)
            assert token
            assert c.is_authenticated


# ---- Profile tests ----


class TestAPIClientProfile:
    def test_get_profile(self, authed_client):
        profile = authed_client.get_profile()
        assert isinstance(profile, UserProfile)
        assert profile.email
        assert profile.username


# ---- Kafka credentials tests ----


class TestAPIClientKafkaCredentials:
    def test_list_kafka_credentials(self, authed_client):
        creds = authed_client.list_kafka_credentials()
        assert isinstance(creds, list)
        for c in creds:
            assert isinstance(c, KafkaCredential)

    def test_create_and_delete_kafka_credential(self, authed_client):
        cred = authed_client.create_kafka_credential("test-cred-integration")
        assert isinstance(cred, KafkaCredential)
        assert cred.name == "test-cred-integration"
        assert cred.kafka_username
        assert cred.kafka_password

        deleted = authed_client.delete_kafka_credential(cred.id)
        assert deleted is True


# ---- Alert tests ----


class TestAPIClientAlerts:
    def test_get_ztf_alerts_empty_query(self, authed_client):
        alerts = authed_client.get_alerts("ztf")
        assert isinstance(alerts, list)
        for a in alerts:
            assert isinstance(a, BabamulZtfAlert)

    def test_get_lsst_alerts_empty_query(self, authed_client):
        alerts = authed_client.get_alerts("lsst")
        assert isinstance(alerts, list)
        for a in alerts:
            assert isinstance(a, BabamulLsstAlert)

    def test_get_ztf_alerts_by_object_id(self, authed_client):
        alerts = authed_client.get_alerts("ztf")
        if not alerts:
            pytest.skip("No ZTF alerts in database")
        object_id = alerts[0].objectId
        filtered = authed_client.get_alerts("ztf", object_id=object_id)
        assert len(filtered) >= 1
        assert all(a.objectId == object_id for a in filtered)

    def test_cone_search(self, authed_client):
        alerts = authed_client.get_alerts("ztf")
        if not alerts:
            pytest.skip("No ZTF alerts in database")
        ra = alerts[0].candidate.ra
        dec = alerts[0].candidate.dec
        results = authed_client.cone_search(
            "ztf", ra=ra, dec=dec, radius_arcsec=60.0
        )
        assert isinstance(results, list)
        assert len(results) >= 1

    def test_get_alerts_with_filters(self, authed_client):
        alerts = authed_client.get_alerts("ztf", min_drb=0.5, max_magpsf=20.0)
        assert isinstance(alerts, list)
        for a in alerts:
            if a.candidate.drb is not None:
                assert a.candidate.drb >= 0.5
            if a.candidate.magpsf is not None:
                assert a.candidate.magpsf <= 20.0


# ---- Cutout tests ----


class TestAPIClientCutouts:
    def test_get_cutouts(self, authed_client):
        alerts = authed_client.get_alerts("ztf")
        if not alerts:
            pytest.skip("No ZTF alerts in database")
        candid = alerts[0].candid
        cutouts = authed_client.get_cutouts("ztf", candid)
        assert isinstance(cutouts, AlertCutouts)
        assert cutouts.candid == candid
        assert (
            cutouts.cutoutScience is not None
            or cutouts.cutoutTemplate is not None
            or cutouts.cutoutDifference is not None
        )

    def test_get_cutouts_for_alert(self, authed_client):
        alerts = authed_client.get_alerts("ztf")
        if not alerts:
            pytest.skip("No ZTF alerts in database")
        alert = alerts[0]
        cutouts = authed_client.get_cutouts_for_alert(alert)
        assert isinstance(cutouts, AlertCutouts)
        assert cutouts.candid == alert.candid

    def test_cutouts_are_bytes(self, authed_client):
        alerts = authed_client.get_alerts("ztf")
        if not alerts:
            pytest.skip("No ZTF alerts in database")
        cutouts = authed_client.get_cutouts("ztf", alerts[0].candid)
        if cutouts.cutoutScience is not None:
            assert isinstance(cutouts.cutoutScience, bytes)
        if cutouts.cutoutTemplate is not None:
            assert isinstance(cutouts.cutoutTemplate, bytes)
        if cutouts.cutoutDifference is not None:
            assert isinstance(cutouts.cutoutDifference, bytes)

    def test_get_cutouts_not_found(self, authed_client):
        with pytest.raises(APINotFoundError):
            authed_client.get_cutouts("ztf", 999999999999999)


# ---- Object tests ----


class TestAPIClientObjects:
    def test_get_ztf_object(self, authed_client):
        alerts = authed_client.get_alerts("ztf")
        if not alerts:
            pytest.skip("No ZTF alerts in database")
        object_id = alerts[0].objectId
        obj = authed_client.get_object("ztf", object_id)
        assert isinstance(obj, BabamulZtfAlert)
        assert obj.objectId == object_id

    def test_get_object_has_photometry(self, authed_client):
        alerts = authed_client.get_alerts("ztf")
        if not alerts:
            pytest.skip("No ZTF alerts in database")
        obj = authed_client.get_object("ztf", alerts[0].objectId)
        phot = obj.get_photometry()
        assert isinstance(phot, list)

    def test_get_object_for_alert(self, authed_client):
        alerts = authed_client.get_alerts("ztf")
        if not alerts:
            pytest.skip("No ZTF alerts in database")
        alert = alerts[0]
        obj = authed_client.get_object_for_alert(alert)
        assert isinstance(obj, BabamulZtfAlert)
        assert obj.objectId == alert.objectId

    def test_get_object_not_found(self, authed_client):
        with pytest.raises(APINotFoundError):
            authed_client.get_object("ztf", "ZTFnonexistent99999")


# ---- Object search tests ----


class TestAPIClientSearch:
    def test_search_objects(self, authed_client):
        alerts = authed_client.get_alerts("ztf")
        if not alerts:
            pytest.skip("No ZTF alerts in database")
        partial_id = alerts[0].objectId[:8]
        results = authed_client.search_objects(partial_id)
        assert isinstance(results, list)
        for r in results:
            assert isinstance(r, ObjectSearchResult)

    def test_search_objects_with_limit(self, authed_client):
        results = authed_client.search_objects("ZTF", limit=3)
        assert isinstance(results, list)
        assert len(results) <= 3

    def test_search_objects_no_results(self, authed_client):
        results = authed_client.search_objects("XXXXXXXXNONEXISTENT")
        assert results == []
