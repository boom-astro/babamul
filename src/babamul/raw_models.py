"""Pydantic raw models for ZTF and LSST alerts, generated from avro schemas."""

from enum import Enum

import numpy as np
from pydantic import AliasChoices, BaseModel, Field, field_validator


class Band(str, Enum):
    g = "g"
    r = "r"
    i = "i"
    z = "z"
    y = "y"
    u = "u"


LSST_ZP = 8.9
ZTF_ZP = 23.9


def flux2mag(flux: float, flux_err: float, zp: float) -> tuple[float, float]:
    """Convert flux and flux error to magnitude and magnitude error.

    Parameters
    ----------
    flux : float
        The flux value.
    flux_err : float
        The error on the flux value.
    zp : float
        The zero point magnitude for the survey.

    Returns
    -------
    mag : float
        The magnitude corresponding to the flux.
    mag_err : float
        The error on the magnitude.
    """
    if flux <= 0:
        return float("inf"), 0.0  # non-detection or negative flux
    mag = zp - 2.5 * np.log10(flux)
    mag_err = (2.5 / np.log(10)) * (flux_err / flux)
    return mag, mag_err


def fluxerr2diffmaglim(flux_err: float, zp: float) -> float:
    """Convert flux error to difference magnitude limit.

    Parameters
    ----------
    flux_err : float
        The error on the flux value.
    zp : float
        The zero point magnitude for the survey.

    Returns
    -------
    diffmaglim : float
        The difference magnitude limit corresponding to the flux error.
    """
    if flux_err <= 0:
        return float("inf")  # non-detection or negative flux error
    diffmaglim = zp - 2.5 * np.log10(3 * flux_err)  # 3-sigma limit
    return diffmaglim


class ZtfCandidate(BaseModel):
    jd: float
    fid: int = Field(..., ge=-(2**31), le=(2**31 - 1))
    pid: int
    diffmaglim: float | None
    programpi: str | None
    programid: int = Field(..., ge=-(2**31), le=(2**31 - 1))
    candid: int
    isdiffpos: bool
    nid: int | None
    rcid: int | None
    field: int | None
    ra: float
    dec: float
    magpsf: float
    sigmapsf: float
    chipsf: float | None
    magap: float | None
    sigmagap: float | None
    distnr: float | None
    magnr: float | None
    sigmagnr: float | None
    chinr: float | None
    sharpnr: float | None
    sky: float | None
    fwhm: float | None
    classtar: float | None
    mindtoedge: float | None
    seeratio: float | None
    aimage: float | None
    bimage: float | None
    elong: float | None
    nneg: int | None
    nbad: int | None
    rb: float | None
    ssdistnr: float | None
    ssmagnr: float | None
    ssnamenr: str | None = None
    ranr: float
    decnr: float
    sgmag1: float | None
    srmag1: float | None
    simag1: float | None
    szmag1: float | None
    sgscore1: float | None
    distpsnr1: float | None
    ndethist: int = Field(..., ge=-(2**31), le=(2**31 - 1))
    ncovhist: int = Field(..., ge=-(2**31), le=(2**31 - 1))
    jdstarthist: float | None = None
    scorr: float | None
    sgmag2: float | None
    srmag2: float | None
    simag2: float | None
    szmag2: float | None
    sgscore2: float | None
    distpsnr2: float | None
    sgmag3: float | None
    srmag3: float | None
    simag3: float | None
    szmag3: float | None
    sgscore3: float | None
    distpsnr3: float | None
    nmtchps: int = Field(..., ge=-(2**31), le=(2**31 - 1))
    dsnrms: float | None
    ssnrms: float | None
    dsdiff: float | None
    magzpsci: float | None
    magzpsciunc: float | None
    magzpscirms: float | None
    zpmed: float | None
    exptime: float | None
    drb: float | None
    clrcoeff: float | None
    clrcounc: float | None
    neargaia: float | None
    maggaia: float | None
    neargaiabright: float | None
    maggaiabright: float | None
    psfFlux: float
    psfFluxErr: float
    snr: float
    band: Band


# class ZtfPhotometry(BaseModel):
#     jd: float
#     magpsf: float | None = None
#     sigmapsf: float | None = None
#     diffmaglim: float
#     psfFlux: float | None = None
#     psfFluxErr: float
#     band: Band
#     zp: float | None = None
#     ra: float | None = None
#     dec: float | None = None
#     snr: float | None = None


class AlertPhotometry(BaseModel):
    jd: float
    psfFlux: float | None = None
    psfFluxErr: float
    band: Band
    ra: float
    dec: float


class NonDetectionPhotometry(BaseModel):
    jd: float
    psfFluxErr: float
    band: Band


class ForcedPhotometry(BaseModel):
    jd: float
    psfFlux: float | None = None
    psfFluxErr: float
    band: Band


# let's rewrite ZtfPhotoetry, that gets automatically deserialized from AlertPhotometry, or NonDetectionPhotometry, or ForcedPhotometry
# on deserialize, we compute the magpsf, sigmapsf, diffmaglim, and snr, using the flux2mag and fluxerr2diffmaglim functions, and the appropriate zero point for ZTF or LSST
class Photometry(BaseModel):
    jd: float
    magpsf: float | None = None
    sigmapsf: float | None = None
    isdiffpos: bool | None = None
    diffmaglim: float | None = None
    psfFlux: float | None = None
    psfFluxErr: float
    band: Band
    zp: float | None = None
    ra: float | None = None
    dec: float | None = None
    snr: float | None = None

    @classmethod
    def from_alert_photometry(cls, photometry: dict, survey_zp: float):
        photometry: AlertPhotometry = AlertPhotometry.model_validate(
            photometry
        )
        magpsf, sigmapsf = flux2mag(
            abs(photometry.psfFlux * 1e-9),
            photometry.psfFluxErr * 1e-9,
            survey_zp,
        )
        snr = (
            abs(photometry.psfFlux) / photometry.psfFluxErr
            if photometry.psfFluxErr > 0
            else 0
        )
        return cls(
            jd=photometry.jd,
            magpsf=magpsf,
            sigmapsf=sigmapsf,
            isdiffpos=photometry.psfFlux > 0,
            psfFlux=photometry.psfFlux,
            psfFluxErr=photometry.psfFluxErr,
            band=photometry.band,
            zp=survey_zp,
            ra=photometry.ra,
            dec=photometry.dec,
            snr=snr,
        )

    @classmethod
    def from_non_detection_photometry(cls, photometry: dict, survey_zp: float):
        photometry: NonDetectionPhotometry = (
            NonDetectionPhotometry.model_validate(photometry)
        )
        diffmaglim = fluxerr2diffmaglim(
            photometry.psfFluxErr * 1e-9, survey_zp
        )
        return cls(
            jd=photometry.jd,
            magpsf=None,
            sigmapsf=None,
            isdiffpos=None,
            diffmaglim=diffmaglim,
            psfFlux=None,
            psfFluxErr=photometry.psfFluxErr,
            band=photometry.band,
            zp=survey_zp,
            ra=None,
            dec=None,
            snr=None,
        )

    @classmethod
    def from_forced_photometry(cls, photometry: dict, survey_zp: float):
        photometry: ForcedPhotometry = ForcedPhotometry.model_validate(
            photometry
        )
        snr = (
            abs(photometry.psfFlux) / photometry.psfFluxErr
            if photometry.psfFluxErr > 0
            else 0
        )
        if snr < 3:
            magpsf = None
            sigmapsf = None
            diffmaglim = fluxerr2diffmaglim(
                photometry.psfFluxErr * 1e-9, survey_zp
            )
        else:
            magpsf, sigmapsf = flux2mag(
                abs(photometry.psfFlux * 1e-9),
                photometry.psfFluxErr * 1e-9,
                survey_zp,
            )
            diffmaglim = None
        return cls(
            jd=photometry.jd,
            magpsf=magpsf,
            sigmapsf=sigmapsf,
            diffmaglim=diffmaglim,
            psfFlux=photometry.psfFlux,
            psfFluxErr=photometry.psfFluxErr,
            band=photometry.band,
            zp=survey_zp,
            ra=None,
            dec=None,
            snr=snr,
        )

    @property
    def datetime(self):
        from astropy import timezone
        from astropy.time import Time

        return Time(self.jd, format="jd").to_datetime(timezone=timezone.utc)


class BandRateProperties(BaseModel):
    rate: float
    rate_error: float
    red_chi2: float | None
    nb_data: int = Field(..., ge=-(2**31), le=(2**31 - 1))
    dt: float


class BandProperties(BaseModel):
    peak_jd: float
    peak_mag: float
    peak_mag_err: float
    dt: float
    rising: BandRateProperties | None
    fading: BandRateProperties | None


class PerBandProperties(BaseModel):
    g: BandProperties | None
    r: BandProperties | None
    i: BandProperties | None
    z: BandProperties | None
    y: BandProperties | None
    u: BandProperties | None


class ZtfAlertProperties(BaseModel):
    rock: bool
    star: bool
    near_brightstar: bool
    stationary: bool
    photstats: PerBandProperties
    multisurvey_photstats: PerBandProperties | None


# class LsstPhotometry(BaseModel):
#     jd: float
#     magpsf: float | None
#     sigmapsf: float | None
#     diffmaglim: float
#     psfFlux: float | None
#     psfFluxErr: float
#     band: Band
#     zp: float | None = None
#     ra: float | None
#     dec: float | None
#     snr: float | None


class LsstMatch(BaseModel):
    objectId: str = Field(..., alias=AliasChoices("objectId", "object_id"))
    ra: float
    dec: float
    prv_candidates: list[Photometry]
    fp_hists: list[Photometry]

    @field_validator("prv_candidates", mode="before")
    @classmethod
    def transform_photometry(cls, v):
        """Transform AlertPhotometry dicts to Photometry instances."""
        if isinstance(v, list):
            return [
                Photometry.from_alert_photometry(item, LSST_ZP)
                if isinstance(item, dict)
                else item
                for item in v
            ]
        return v

    @field_validator("fp_hists", mode="before")
    @classmethod
    def transform_forced_photometry(cls, v):
        """Transform ForcedPhotometry dicts to Photometry instances."""
        if isinstance(v, list):
            return [
                Photometry.from_forced_photometry(item, LSST_ZP)
                if isinstance(item, dict)
                else item
                for item in v
            ]
        return v


class ZtfSurveyMatches(BaseModel):
    lsst: LsstMatch | None


class EnrichedZtfAlert(BaseModel):
    candid: int = Field(..., alias=AliasChoices("candid", "_id"))
    objectId: str = Field(..., alias=AliasChoices("objectId", "object_id"))
    candidate: ZtfCandidate
    prv_candidates: list[Photometry] | None = None
    prv_nondetections: list[Photometry] | None = None
    fp_hists: list[Photometry] | None = None
    properties: ZtfAlertProperties
    survey_matches: ZtfSurveyMatches | None = None
    cutoutScience: bytes | None = Field(
        None, alias=AliasChoices("cutoutScience", "cutout_science")
    )
    cutoutTemplate: bytes | None = Field(
        None, alias=AliasChoices("cutoutTemplate", "cutout_template")
    )
    cutoutDifference: bytes | None = Field(
        None, alias=AliasChoices("cutoutDifference", "cutout_difference")
    )

    @field_validator("prv_candidates", mode="before")
    @classmethod
    def transform_photometry(cls, v):
        """Transform AlertPhotometry dicts to Photometry instances."""
        if isinstance(v, list):
            return [
                Photometry.from_alert_photometry(item, ZTF_ZP)
                if isinstance(item, dict)
                else item
                for item in v
            ]
        return v

    @field_validator("prv_nondetections", mode="before")
    @classmethod
    def transform_non_detections(cls, v):
        """Transform NonDetectionPhotometry dicts to Photometry instances."""
        if isinstance(v, list):
            return [
                Photometry.from_non_detection_photometry(item, ZTF_ZP)
                if isinstance(item, dict)
                else item
                for item in v
            ]
        return v

    @field_validator("fp_hists", mode="before")
    @classmethod
    def transform_forced_photometry(cls, v):
        """Transform ForcedPhotometry dicts to Photometry instances."""
        if isinstance(v, list):
            return [
                Photometry.from_forced_photometry(item, ZTF_ZP)
                if isinstance(item, dict)
                else item
                for item in v
            ]
        return v


class LsstCandidate(BaseModel):
    diaSourceId: int
    visit: int
    detector: int = Field(..., ge=-(2**31), le=(2**31 - 1))
    diaObjectId: int | None = None
    ssObjectId: int | None = None
    parentDiaSourceId: int | None
    midpointMjdTai: float
    ra: float
    raErr: float | None = None
    dec: float
    decErr: float | None
    centroid_flag: bool | None
    apFlux: float | None
    apFluxErr: float | None
    apFlux_flag: bool | None
    apFlux_flag_apertureTruncated: bool | None
    psfFlux: float | None
    psfFluxErr: float | None
    psfChi2: float | None
    psfNdata: int | None
    psfFlux_flag: bool | None
    psfFlux_flag_edge: bool | None
    psfFlux_flag_noGoodPixels: bool | None
    trailFlux: float | None
    trailFluxErr: float | None
    trailRa: float | None
    trailRaErr: float | None
    trailDec: float | None
    trailDecErr: float | None
    trailLength: float | None
    trailLengthErr: float | None
    trailAngle: float | None
    trailAngleErr: float | None
    trailChi2: float | None
    trailNdata: int | None
    trail_flag_edge: bool | None
    scienceFlux: float | None
    scienceFluxErr: float | None
    forced_PsfFlux_flag: bool | None
    forced_PsfFlux_flag_edge: bool | None
    forced_PsfFlux_flag_noGoodPixels: bool | None
    templateFlux: float | None
    templateFluxErr: float | None
    shape_flag: bool | None
    shape_flag_no_pixels: bool | None
    shape_flag_not_contained: bool | None
    shape_flag_parent_source: bool | None
    extendedness: float | None
    reliability: float | None
    band: Band | None
    isDipole: bool | None
    pixelFlags: bool | None
    pixelFlags_bad: bool | None
    pixelFlags_cr: bool | None
    pixelFlags_crCenter: bool | None
    pixelFlags_edge: bool | None
    pixelFlags_nodata: bool | None
    pixelFlags_nodataCenter: bool | None
    pixelFlags_interpolated: bool | None
    pixelFlags_interpolatedCenter: bool | None
    pixelFlags_offimage: bool | None
    pixelFlags_saturated: bool | None
    pixelFlags_saturatedCenter: bool | None
    pixelFlags_suspect: bool | None
    pixelFlags_suspectCenter: bool | None
    pixelFlags_streak: bool | None
    pixelFlags_streakCenter: bool | None
    pixelFlags_injected: bool | None
    pixelFlags_injectedCenter: bool | None
    pixelFlags_injected_template: bool | None
    pixelFlags_injected_templateCenter: bool | None
    glint_trail: bool | None
    objectId: str = Field(..., alias=AliasChoices("objectId", "object_id"))
    jd: float
    magpsf: float
    sigmapsf: float
    diffmaglim: float
    isdiffpos: bool
    snr: float
    magap: float
    sigmagap: float
    jdstarthist: float | None = None
    ndethist: int | None = None


class LsstAlertProperties(BaseModel):
    rock: bool
    stationary: bool
    star: bool | None = None
    near_brightstar: bool | None = None
    photstats: PerBandProperties
    multisurvey_photstats: PerBandProperties


class ZtfMatch(BaseModel):
    objectId: str = Field(..., alias=AliasChoices("objectId", "object_id"))
    ra: float
    dec: float
    prv_candidates: list[Photometry]
    prv_nondetections: list[Photometry]
    fp_hists: list[Photometry]

    @field_validator("prv_candidates", mode="before")
    @classmethod
    def transform_photometry(cls, v):
        """Transform AlertPhotometry dicts to Photometry instances."""
        if isinstance(v, list):
            return [
                Photometry.from_alert_photometry(item, ZTF_ZP)
                if isinstance(item, dict)
                else item
                for item in v
            ]
        return v

    @field_validator("prv_nondetections", mode="before")
    @classmethod
    def transform_non_detections(cls, v):
        """Transform NonDetectionPhotometry dicts to Photometry instances."""
        if isinstance(v, list):
            return [
                Photometry.from_non_detection_photometry(item, ZTF_ZP)
                if isinstance(item, dict)
                else item
                for item in v
            ]
        return v

    @field_validator("fp_hists", mode="before")
    @classmethod
    def transform_forced_photometry(cls, v):
        """Transform ForcedPhotometry dicts to Photometry instances."""
        if isinstance(v, list):
            return [
                Photometry.from_forced_photometry(item, ZTF_ZP)
                if isinstance(item, dict)
                else item
                for item in v
            ]
        return v


class LsstSurveyMatches(BaseModel):
    ztf: ZtfMatch | None


class EnrichedLsstAlert(BaseModel):
    candid: int = Field(..., alias=AliasChoices("candid", "_id"))
    objectId: str = Field(..., alias=AliasChoices("objectId", "object_id"))
    candidate: LsstCandidate
    prv_candidates: list[Photometry] | None = None
    fp_hists: list[Photometry] | None = None
    properties: LsstAlertProperties
    cutoutScience: bytes | None = Field(
        None, alias=AliasChoices("cutoutScience", "cutout_science")
    )
    cutoutTemplate: bytes | None = Field(
        None, alias=AliasChoices("cutoutTemplate", "cutout_template")
    )
    cutoutDifference: bytes | None = Field(
        None, alias=AliasChoices("cutoutDifference", "cutout_difference")
    )
    survey_matches: LsstSurveyMatches | None = None

    @field_validator("prv_candidates", mode="before")
    @classmethod
    def transform_photometry(cls, v):
        """Transform AlertPhotometry dicts to Photometry instances."""
        if isinstance(v, list):
            return [
                Photometry.from_alert_photometry(item, LSST_ZP)
                if isinstance(item, dict)
                else item
                for item in v
            ]
        return v

    @field_validator("fp_hists", mode="before")
    @classmethod
    def transform_forced_photometry(cls, v):
        """Transform ForcedPhotometry dicts to Photometry instances."""
        if isinstance(v, list):
            return [
                Photometry.from_forced_photometry(item, LSST_ZP)
                if isinstance(item, dict)
                else item
                for item in v
            ]
        return v
