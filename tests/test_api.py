"""Tests for the babamul.api.APIClient class."""
import os
import dotenv
import pytest

from dataclasses import dataclass
from babamul.api import (
    APIClient,
    AlertCutouts,
    KafkaCredential,
    ObjectSearchResult,
    UserProfile,
)
from babamul.config import API_URLS
from babamul.exceptions import (
    APIAuthenticationError,
    APIError,
    APINotFoundError,
)
from babamul.models import ZtfAlert, LsstAlert
from babamul.consumer import AlertConsumer

dotenv.load_dotenv()


# ---- Fixtures ----


@dataclass
class _TestObject:
    id: str
    ra: float
    dec: float


def _get_test_object(client, survey, object_id):
    if object_id is None:
        pytest.skip(f"{survey.upper()}_OBJECT_ID environment variable not set")
    obj = client.get_object(survey, object_id)
    if obj is None:
        pytest.skip(f"Object {object_id} not found in survey {survey}")
    if obj.candidate and obj.candidate.ra is not None and obj.candidate.dec is not None:
        return _TestObject(object_id, obj.candidate.ra, obj.candidate.dec)
    else:
        pytest.skip(f"Could not retrieve coordinates for {survey} object ID {object_id}")


@pytest.fixture(scope="session")
def authed_client():
    """Session-scoped authenticated APIClient."""
    email = os.environ.get("EMAIL")
    password = os.environ.get("PASSWORD")
    if not email or not password:
        pytest.skip("EMAIL and PASSWORD environment variables must be set for authenticated tests")
    client = APIClient()
    client.login(email, password)
    yield client
    client.close()


@pytest.fixture
def client():
    """Unauthenticated APIClient."""
    c = APIClient()
    yield c
    c.close()


@pytest.fixture(scope="session")
def ztf_object(authed_client):
    return _get_test_object(authed_client, "ztf", os.environ.get("ZTF_OBJECT_ID"))


@pytest.fixture(scope="session")
def lsst_object(authed_client):
    return _get_test_object(authed_client, "lsst", os.environ.get("LSST_OBJECT_ID"))


# ---- Initialization tests ----


class TestAPIClientInit:
    def test_context_manager(self):
        with APIClient() as c:
            assert not c.is_authenticated

    def test_no_token_by_default(self, client):
        assert not client.is_authenticated

    def test_base_url_stored(self, client):
        assert client._base_url == API_URLS[os.getenv("BABAMUL_ENV", "production").lower()]

    def test_requires_auth_without_token(self, client):
        with pytest.raises(
            APIAuthenticationError, match="Authentication required"
        ):
            client._request("GET", "/profile")


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
        try:
            assert isinstance(cred, KafkaCredential)
            assert cred.name == "test-cred-integration"
            assert cred.kafka_username
            assert cred.kafka_password
        finally:
            deleted = authed_client.delete_kafka_credential(cred.id)
            assert deleted is True


# ---- Alert tests ----


class TestAPIClientAlerts:
    def test_get_alerts_requires_filter(self, authed_client):
        with pytest.raises(ValueError, match="object_id or \\(ra, dec, radius_arcsec\\)"):
            authed_client.get_alerts("ztf")
        with pytest.raises(ValueError, match="object_id or \\(ra, dec, radius_arcsec\\)"):
            authed_client.get_alerts("lsst")

    def test_get_ztf_alerts_by_object_id(self, authed_client, ztf_object):
        alerts = authed_client.get_alerts("ztf", object_id=ztf_object.id)
        assert len(alerts) >= 1
        assert all(a.objectId == ztf_object.id for a in alerts)

    def test_get_lsst_alerts_by_object_id(self, authed_client, lsst_object):
        alerts = authed_client.get_alerts("lsst", object_id=lsst_object.id)
        assert len(alerts) >= 1
        assert all(a.objectId == lsst_object.id for a in alerts)

    def test_get_ztf_alerts_by_ra_dec(self, authed_client, ztf_object):
        alerts = authed_client.get_alerts("ztf", ra=ztf_object.ra, dec=ztf_object.dec, radius_arcsec=10.0)
        assert len(alerts) >= 1
        for a in alerts:
            # Simple check: ensure the alert is within ~10 arcsec of the target position
            delta_ra = abs(a.candidate.ra - ztf_object.ra)
            delta_dec = abs(a.candidate.dec - ztf_object.dec)
            assert (delta_ra**2 + delta_dec**2)**0.5 <= (10.0 / 3600.0)

    def test_get_lsst_alerts_by_ra_dec(self, authed_client, lsst_object):
        alerts = authed_client.get_alerts("lsst", ra=lsst_object.ra, dec=lsst_object.dec, radius_arcsec=10.0)
        assert len(alerts) >= 1
        for a in alerts:
            # Simple check: ensure the alert is within ~10 arcsec of the target position
            delta_ra = abs(a.candidate.ra - lsst_object.ra)
            delta_dec = abs(a.candidate.dec - lsst_object.dec)
            assert (delta_ra**2 + delta_dec**2)**0.5 <= (10.0 / 3600.0)

    def test_get_alerts_with_drb_filters(self, authed_client, ztf_object):
        not_filtered_alerts = authed_client.get_alerts("ztf", object_id=ztf_object.id)
        assert len(not_filtered_alerts) >= 1

        min_drb = 0.99
        is_drb_below = any(
            a.candidate.drb is not None and a.candidate.drb < min_drb for a in not_filtered_alerts
        )
        if is_drb_below:
            alerts = authed_client.get_alerts("ztf", object_id=ztf_object.id, min_drb=min_drb, max_drb=1)
            for a in alerts:
                if a.candidate.drb is not None:
                    assert a.candidate.drb >= min_drb
            assert len(not_filtered_alerts) > len(alerts)
        else:
            pytest.skip(f"No alerts with drb < {min_drb} to test filtering")

    def test_get_alerts_with_magpsf_filters(self, authed_client, ztf_object):
        not_filtered_alerts = authed_client.get_alerts("ztf", object_id=ztf_object.id)
        assert len(not_filtered_alerts) >= 1

        min_magpsf = 18.0
        is_magpsf_below = any(
            a.candidate.magpsf is not None and a.candidate.magpsf < min_magpsf for a in not_filtered_alerts
        )
        if is_magpsf_below:
            alerts = authed_client.get_alerts("ztf", object_id=ztf_object.id, min_magpsf=min_magpsf, max_magpsf=30.0)
            for a in alerts:
                if a.candidate.magpsf is not None:
                    assert a.candidate.magpsf >= min_magpsf
            assert len(not_filtered_alerts) > len(alerts)
        else:
            pytest.skip(f"No alerts with magpsf < {min_magpsf} to test filtering")


# ---- Cutout tests ----


class TestAPIClientCutouts:
    def test_get_ztf_cutouts(self, authed_client, ztf_object):
        alerts = authed_client.get_alerts("ztf", object_id=ztf_object.id)
        candid = alerts[0].candid
        cutouts = authed_client.get_cutouts("ztf", candid)
        assert isinstance(cutouts, AlertCutouts)
        assert cutouts.candid == candid
        assert (
            cutouts.cutoutScience is not None
            or cutouts.cutoutTemplate is not None
            or cutouts.cutoutDifference is not None
        )

    def test_get_lsst_cutouts(self, authed_client, lsst_object):
        alerts = authed_client.get_alerts("lsst", object_id=lsst_object.id)
        candid = alerts[0].candid
        cutouts = authed_client.get_cutouts("lsst", candid)
        assert isinstance(cutouts, AlertCutouts)
        assert cutouts.candid == candid
        assert (
            cutouts.cutoutScience is not None
            or cutouts.cutoutTemplate is not None
            or cutouts.cutoutDifference is not None
        )

    def test_get_ztf_cutouts_for_alert(self, authed_client, ztf_object):
        alerts = authed_client.get_alerts("ztf", object_id=ztf_object.id)
        alert = alerts[0]
        cutouts = alert.fetch_cutouts(authed_client)
        assert isinstance(cutouts, AlertCutouts)
        assert cutouts.candid == alert.candid

    def test_get_lsst_cutouts_for_alert(self, authed_client, lsst_object):
        alerts = authed_client.get_alerts("lsst", object_id=lsst_object.id)
        alert = alerts[0]
        cutouts = alert.fetch_cutouts(authed_client)
        assert isinstance(cutouts, AlertCutouts)
        assert cutouts.candid == alert.candid

    def test_ztf_cutouts_are_bytes(self, authed_client, ztf_object):
        alerts = authed_client.get_alerts("ztf", object_id=ztf_object.id)
        cutouts = alerts[0].fetch_cutouts(authed_client)
        if cutouts.cutoutScience is not None:
            assert isinstance(cutouts.cutoutScience, bytes)
        if cutouts.cutoutTemplate is not None:
            assert isinstance(cutouts.cutoutTemplate, bytes)
        if cutouts.cutoutDifference is not None:
            assert isinstance(cutouts.cutoutDifference, bytes)

    def test_lsst_cutouts_are_bytes(self, authed_client, lsst_object):
        alerts = authed_client.get_alerts("lsst", object_id=lsst_object.id)
        cutouts = alerts[0].fetch_cutouts(authed_client)
        if cutouts.cutoutScience is not None:
            assert isinstance(cutouts.cutoutScience, bytes)
        if cutouts.cutoutTemplate is not None:
            assert isinstance(cutouts.cutoutTemplate, bytes)
        if cutouts.cutoutDifference is not None:
            assert isinstance(cutouts.cutoutDifference, bytes)

    def test_get_ztf_cutouts_not_found(self, authed_client):
        with pytest.raises(APINotFoundError):
            authed_client.get_cutouts("ztf", 999999999999999)

    def test_get_lsst_cutouts_not_found(self, authed_client):
        with pytest.raises(APINotFoundError):
            authed_client.get_cutouts("lsst", 999999999999999)


# ---- Object tests ----


class TestAPIClientObjects:
    def test_get_ztf_object(self, authed_client, ztf_object):
        obj = authed_client.get_object("ztf", ztf_object.id)
        assert isinstance(obj, ZtfAlert)
        assert obj.objectId == ztf_object.id

    def test_get_lsst_object(self, authed_client, lsst_object):
        obj = authed_client.get_object("lsst", lsst_object.id)
        assert isinstance(obj, LsstAlert)
        assert obj.objectId == lsst_object.id

    def test_get_ztf_object_has_photometry(self, authed_client, ztf_object):
        obj = authed_client.get_object("ztf", ztf_object.id)
        phot = obj.get_photometry()
        assert isinstance(phot, list)

    def test_get_lsst_object_has_photometry(self, authed_client, lsst_object):
        obj = authed_client.get_object("lsst", lsst_object.id)
        phot = obj.get_photometry()
        assert isinstance(phot, list)

    def test_get_ztf_object_from_alert(self, authed_client, ztf_object):
        alerts = authed_client.get_alerts("ztf", object_id=ztf_object.id)
        alert = alerts[0]
        obj = alert.fetch_object(authed_client)
        assert isinstance(obj, ZtfAlert)
        assert obj.objectId == ztf_object.id

    def test_get_lsst_object_from_alert(self, authed_client, lsst_object):
        alerts = authed_client.get_alerts("lsst", object_id=lsst_object.id)
        alert = alerts[0]
        obj = alert.fetch_object(authed_client)
        assert isinstance(obj, LsstAlert)
        assert obj.objectId == lsst_object.id

    def test_get_ztf_object_not_found(self, authed_client):
        with pytest.raises(APINotFoundError):
            authed_client.get_object("ztf", "ZTFnonexistent99999")

    def test_get_lsst_object_not_found(self, authed_client):
        with pytest.raises(APINotFoundError):
            authed_client.get_object("lsst", "lsstnonexistent99999")


# ---- Object search tests ----


class TestAPIClientSearch:
    def test_ztf_search_objects(self, authed_client, ztf_object):
        results = authed_client.search_objects(ztf_object.id[:11], limit=100)
        assert isinstance(results, list)
        for r in results:
            assert isinstance(r, ObjectSearchResult)

        if len(results) < 100:
            assert any(r.objectId == ztf_object.id for r in results), "Expected object ID not found in search results"
        else:
            pytest.skip("Too many ZTF results to guarantee presence of specific object ID")

    def test_ztf_search_objects_with_limit(self, authed_client):
        results = authed_client.search_objects("ZTF", limit=3)
        assert isinstance(results, list)
        assert len(results) <= 3

    def test_ztf_search_bad_object_id(self, authed_client):
        with pytest.raises(APIError):
            authed_client.search_objects("XXXXXXXXBADID")

    def test_ztf_search_objects_no_results(self, authed_client):
        results = authed_client.search_objects("ZTF10mmmmmmm", limit=10)
        assert isinstance(results, list)
        assert len(results) == 0


# ---- Fetch cutouts from consume kafka alert tests ----


class TestFetchCutoutsFromKafkaAlert:
    @pytest.fixture(scope="class")
    def kafka_cred(self, authed_client):
        """Create a temporary Kafka credential and consumer for this test class."""
        cred = authed_client.create_kafka_credential("test-cred-integration")
        assert isinstance(cred, KafkaCredential)
        assert cred.kafka_username
        assert cred.kafka_password

        try:
            yield cred
        finally:
            deleted = authed_client.delete_kafka_credential(cred.id)
            assert deleted is True

    def test_fetch_ztf_cutouts_from_kafka_alert(self, authed_client, kafka_cred):
        ztf_consumer = AlertConsumer(
            topics="babamul.ztf.no-lsst-match.hosted",
            offset="earliest",
            username=kafka_cred.kafka_username,
            password=kafka_cred.kafka_password,
        )
        for alert in ztf_consumer:
            cutouts = alert.fetch_cutouts(authed_client)
            assert isinstance(cutouts, AlertCutouts)
            assert cutouts.candid == alert.candid
            assert isinstance(cutouts.cutoutScience, bytes)
            assert isinstance(cutouts.cutoutTemplate, bytes)
            assert isinstance(cutouts.cutoutDifference, bytes)
            break

        ztf_consumer.close()

    def test_fetch_lsst_cutouts_from_kafka_alert(self, authed_client, kafka_cred):
        lsst_consumer = AlertConsumer(
            topics="babamul.lsst.no-ztf-match.hostless",
            offset="earliest",
            username=kafka_cred.kafka_username,
            password=kafka_cred.kafka_password,
        )
        for alert in lsst_consumer:
            cutouts = alert.fetch_cutouts(authed_client)
            assert isinstance(cutouts, AlertCutouts)
            assert cutouts.candid == alert.candid
            assert isinstance(cutouts.cutoutScience, bytes)
            assert isinstance(cutouts.cutoutTemplate, bytes)
            assert isinstance(cutouts.cutoutDifference, bytes)
            break

        lsst_consumer.close()
