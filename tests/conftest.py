"""Pytest fixtures for babamul tests."""

from typing import Any

import pytest


@pytest.fixture
def sample_ztf_candidate_dict() -> dict[str, Any]:
    """Sample ZTF candidate data."""
    return {
        "jd": 2460500.5,
        "fid": 1,
        "pid": 1234567890123,
        "diffmaglim": 20.5,
        "programpi": None,
        "programid": 1,
        "candid": 1234567890123,
        "isdiffpos": True,
        "nid": 1234,
        "rcid": 1,
        "field": 123,
        "ra": 150.123456,
        "dec": 30.654321,
        "magpsf": 18.5,
        "sigmapsf": 0.1,
        "chipsf": None,
        "magap": 18.6,
        "sigmagap": 0.15,
        "distnr": 0.5,
        "magnr": 18.0,
        "sigmagnr": 0.05,
        "chinr": None,
        "sharpnr": None,
        "sky": None,
        "fwhm": 2.5,
        "classtar": 0.9,
        "mindtoedge": None,
        "seeratio": None,
        "aimage": None,
        "bimage": None,
        "elong": None,
        "nneg": None,
        "nbad": None,
        "rb": 0.95,
        "ssdistnr": None,
        "ssmagnr": None,
        "ssnamenr": None,
        "ranr": 150.123456,
        "decnr": 30.654321,
        "sgmag1": None,
        "srmag1": None,
        "simag1": None,
        "szmag1": None,
        "sgscore1": None,
        "distpsnr1": None,
        "ndethist": 10,
        "ncovhist": 100,
        "jdstarthist": 2460400.5,
        "scorr": None,
        "sgmag2": None,
        "srmag2": None,
        "simag2": None,
        "szmag2": None,
        "sgscore2": None,
        "distpsnr2": None,
        "sgmag3": None,
        "srmag3": None,
        "simag3": None,
        "szmag3": None,
        "sgscore3": None,
        "distpsnr3": None,
        "nmtchps": 5,
        "dsnrms": None,
        "ssnrms": None,
        "dsdiff": None,
        "magzpsci": 26.0,
        "magzpsciunc": 0.01,
        "magzpscirms": None,
        "zpmed": None,
        "exptime": 30.0,
        "drb": 0.98,
        "clrcoeff": None,
        "clrcounc": None,
        "neargaia": None,
        "maggaia": None,
        "neargaiabright": None,
        "maggaiabright": None,
        "psfFlux": 1000.0,
        "psfFluxErr": 50.0,
        "snr": 20.0,
        "band": "r",
    }


@pytest.fixture
def sample_ztf_photometry_dict() -> dict[str, Any]:
    """Sample ZTF photometry data."""
    return {
        "jd": 2460499.5,
        "magpsf": 18.7,
        "sigmapsf": 0.12,
        "diffmaglim": 20.5,
        "psfFlux": 900.0,
        "psfFluxErr": 45.0,
        "band": "g",
        "zp": 26.0,
        "ra": 150.123456,
        "dec": 30.654321,
        "snr": 18.0,
        "programid": 1,
    }


@pytest.fixture
def sample_ztf_nondetection_dict() -> dict[str, Any]:
    """Sample ZTF non-detection data."""
    return {
        "jd": 2460498.5,
        "magpsf": None,
        "sigmapsf": None,
        "diffmaglim": 19.5,
        "psfFlux": None,
        "psfFluxErr": 100.0,
        "band": "r",
        "zp": 26.0,
        "ra": None,
        "dec": None,
        "snr": None,
        "programid": 1,
    }


@pytest.fixture
def sample_ztf_properties_dict() -> dict[str, Any]:
    """Sample ZTF alert properties."""
    return {
        "rock": False,
        "star": False,
        "near_brightstar": False,
        "stationary": False,
        "photstats": {
            "g": None,
            "r": {
                "peak_jd": 2460500.5,
                "peak_mag": 18.5,
                "peak_mag_err": 0.1,
                "dt": 10.0,
                "rising": None,
                "fading": None,
            },
            "i": None,
            "z": None,
            "y": None,
            "u": None,
        },
        "multisurvey_photstats": None,
    }


@pytest.fixture
def sample_ztf_alert_dict(
    sample_ztf_candidate_dict: dict[str, Any],
    sample_ztf_photometry_dict: dict[str, Any],
    sample_ztf_nondetection_dict: dict[str, Any],
    sample_ztf_properties_dict: dict[str, Any],
) -> dict[str, Any]:
    """Sample ZTF alert data as a dictionary."""
    return {
        "candid": 1234567890123,
        "objectId": "ZTF24aabcdef",
        "candidate": sample_ztf_candidate_dict,
        "prv_candidates": [sample_ztf_photometry_dict],
        "prv_nondetections": [sample_ztf_nondetection_dict],
        "fp_hists": [],
        "properties": sample_ztf_properties_dict,
        "survey_matches": None,
        "cutoutScience": b"\x1f\x8b\x08\x00",  # gzip header
        "cutoutTemplate": b"\x1f\x8b\x08\x00",
        "cutoutDifference": b"\x1f\x8b\x08\x00",
    }


@pytest.fixture
def sample_lsst_candidate_dict() -> dict[str, Any]:
    """Sample LSST candidate data."""
    return {
        "diaSourceId": 9876543210,
        "visit": 12345,
        "detector": 42,
        "diaObjectId": 111222333,
        "ssObjectId": None,
        "parentDiaSourceId": None,
        "midpointMjdTai": 60500.5,
        "ra": 150.123456,
        "raErr": 0.001,
        "dec": 30.654321,
        "decErr": 0.001,
        "centroid_flag": False,
        "apFlux": 1000.0,
        "apFluxErr": 50.0,
        "apFlux_flag": False,
        "apFlux_flag_apertureTruncated": False,
        "psfFlux": 1000.0,
        "psfFluxErr": 50.0,
        "psfChi2": 1.0,
        "psfNdata": 100,
        "psfFlux_flag": False,
        "psfFlux_flag_edge": False,
        "psfFlux_flag_noGoodPixels": False,
        "trailFlux": None,
        "trailFluxErr": None,
        "trailRa": None,
        "trailRaErr": None,
        "trailDec": None,
        "trailDecErr": None,
        "trailLength": None,
        "trailLengthErr": None,
        "trailAngle": None,
        "trailAngleErr": None,
        "trailChi2": None,
        "trailNdata": None,
        "trail_flag_edge": None,
        "scienceFlux": None,
        "scienceFluxErr": None,
        "forced_PsfFlux_flag": None,
        "forced_PsfFlux_flag_edge": None,
        "forced_PsfFlux_flag_noGoodPixels": None,
        "templateFlux": None,
        "templateFluxErr": None,
        "shape_flag": None,
        "shape_flag_no_pixels": None,
        "shape_flag_not_contained": None,
        "shape_flag_parent_source": None,
        "extendedness": 0.1,
        "reliability": 0.95,
        "band": "r",
        "isDipole": False,
        "pixelFlags": False,
        "pixelFlags_bad": False,
        "pixelFlags_cr": False,
        "pixelFlags_crCenter": False,
        "pixelFlags_edge": False,
        "pixelFlags_nodata": False,
        "pixelFlags_nodataCenter": False,
        "pixelFlags_interpolated": False,
        "pixelFlags_interpolatedCenter": False,
        "pixelFlags_offimage": False,
        "pixelFlags_saturated": False,
        "pixelFlags_saturatedCenter": False,
        "pixelFlags_suspect": False,
        "pixelFlags_suspectCenter": False,
        "pixelFlags_streak": False,
        "pixelFlags_streakCenter": False,
        "pixelFlags_injected": False,
        "pixelFlags_injectedCenter": False,
        "pixelFlags_injected_template": False,
        "pixelFlags_injected_templateCenter": False,
        "glint_trail": False,
        "objectId": "LSST24aabcdef",
        "jd": 2460500.5,
        "magpsf": 18.5,
        "sigmapsf": 0.1,
        "diffmaglim": 20.5,
        "isdiffpos": True,
        "snr": 20.0,
        "magap": 18.6,
        "sigmagap": 0.15,
        "jdstarthist": 2460400.5,
        "ndethist": 5,
    }


@pytest.fixture
def sample_lsst_photometry_dict() -> dict[str, Any]:
    """Sample LSST photometry data."""
    return {
        "jd": 2460499.5,
        "magpsf": 18.7,
        "sigmapsf": 0.12,
        "diffmaglim": 20.5,
        "psfFlux": 900.0,
        "psfFluxErr": 45.0,
        "band": "g",
        "zp": 26.0,
        "ra": 150.123456,
        "dec": 30.654321,
        "snr": 18.0,
    }


@pytest.fixture
def sample_lsst_properties_dict() -> dict[str, Any]:
    """Sample LSST alert properties."""
    return {
        "rock": False,
        "stationary": False,
        "star": False,
        "photstats": {
            "g": None,
            "r": {
                "peak_jd": 2460500.5,
                "peak_mag": 18.5,
                "peak_mag_err": 0.1,
                "dt": 10.0,
                "rising": None,
                "fading": None,
            },
            "i": None,
            "z": None,
            "y": None,
            "u": None,
        },
        "multisurvey_photstats": {
            "g": None,
            "r": None,
            "i": None,
            "z": None,
            "y": None,
            "u": None,
        },
    }


@pytest.fixture
def sample_lsst_alert_dict(
    sample_lsst_candidate_dict: dict[str, Any],
    sample_lsst_photometry_dict: dict[str, Any],
    sample_lsst_properties_dict: dict[str, Any],
) -> dict[str, Any]:
    """Sample LSST alert data as a dictionary."""
    return {
        "candid": 9876543210,
        "objectId": "LSST24aabcdef",
        "candidate": sample_lsst_candidate_dict,
        "prv_candidates": [sample_lsst_photometry_dict],
        "fp_hists": [],
        "properties": sample_lsst_properties_dict,
        "survey_matches": None,
        "cutoutScience": b"\x1f\x8b\x08\x00",
        "cutoutTemplate": b"\x1f\x8b\x08\x00",
        "cutoutDifference": b"\x1f\x8b\x08\x00",
    }
