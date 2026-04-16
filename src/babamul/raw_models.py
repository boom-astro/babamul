"""Pydantic raw models for ZTF and LSST alerts, generated from avro schemas."""

from enum import Enum
from typing import Any

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
    return float(diffmaglim)


class ZtfCandidate(BaseModel):
    """ZTF alert candidate data from the ZTF alert stream."""

    jd: float = Field(description="Observation Julian date at start of exposure [days]")
    fid: int = Field(
        ...,
        ge=1,
        le=3,
        description="Filter ID (1=g; 2=R; 3=i)",
    )
    pid: int = Field(
        description="Processing ID for science image to facilitate archive retrieval"
    )
    diffmaglim: float | None = Field(
        None,
        description="Expected 5-sigma mag limit in difference image based on global noise estimate [mag]",
    )
    programpi: str | None = Field(
        None, description="Principal investigator attached to program ID"
    )
    programid: int = Field(
        ...,
        ge=0,
        le=3,
        description="Program ID: 0=engineering, 1=public, 2=partnership, 3=caltech",
    )
    candid: int = Field(description="Candidate ID from operations DB")
    isdiffpos: bool = Field(
        description="True if candidate is from positive (sci minus ref) subtraction; False if from negative (ref minus sci) subtraction"
    )
    nid: int | None = Field(None, description="Night ID")
    rcid: int | None = Field(None, description="Readout channel ID [00 .. 63]")
    field: int | None = Field(None, description="ZTF field ID")
    ra: float = Field(description="Right Ascension of candidate; J2000 [deg]")
    dec: float = Field(description="Declination of candidate; J2000 [deg]")
    magpsf: float = Field(description="Magnitude from PSF-fit photometry [mag]")
    sigmapsf: float = Field(description="1-sigma uncertainty in magpsf [mag]")
    chipsf: float | None = Field(None, description="Reduced chi-square for PSF-fit")
    magap: float | None = Field(
        None, description="Aperture mag using 14 pixel diameter aperture [mag]"
    )
    sigmagap: float | None = Field(
        None, description="1-sigma uncertainty in magap [mag]"
    )
    distnr: float | None = Field(
        None,
        description="Distance to nearest source in reference image PSF-catalog [pixels]",
    )
    magnr: float | None = Field(
        None,
        description="Magnitude of nearest source in reference image PSF-catalog [mag]",
    )
    sigmagnr: float | None = Field(
        None, description="1-sigma uncertainty in magnr [mag]"
    )
    chinr: float | None = Field(
        None,
        description="DAOPhot chi parameter of nearest source in reference image PSF-catalog",
    )
    sharpnr: float | None = Field(
        None,
        description="DAOPhot sharp parameter of nearest source in reference image PSF-catalog",
    )
    sky: float | None = Field(
        None, description="Local sky background estimate [DN]"
    )
    fwhm: float | None = Field(
        None,
        description="Full Width Half Max assuming a Gaussian core, from SExtractor [pixels]",
    )
    classtar: float | None = Field(
        None, description="Star/Galaxy classification score from SExtractor"
    )
    mindtoedge: float | None = Field(
        None, description="Distance to nearest edge in image [pixels]"
    )
    seeratio: float | None = Field(
        None, description="Ratio: difffwhm / fwhm"
    )
    aimage: float | None = Field(
        None,
        description="Windowed profile RMS along major axis from SExtractor [pixels]",
    )
    bimage: float | None = Field(
        None,
        description="Windowed profile RMS along minor axis from SExtractor [pixels]",
    )
    elong: float | None = Field(None, description="Ratio: aimage / bimage")
    nneg: int | None = Field(
        None, description="Number of negative pixels in a 5 x 5 pixel stamp"
    )
    nbad: int | None = Field(
        None,
        description="Number of prior-tagged bad pixels in a 5 x 5 pixel stamp",
    )
    rb: float | None = Field(
        None,
        description="RealBogus quality score from Random Forest classifier; range is 0 to 1 where closer to 1 is more reliable",
    )
    ssdistnr: float | None = Field(
        None,
        description="Distance to nearest known solar system object if exists within 30 arcsec [arcsec]",
    )
    ssmagnr: float | None = Field(
        None,
        description="Magnitude of nearest known solar system object if exists within 30 arcsec [mag]",
    )
    ssnamenr: str | None = Field(
        None,
        description="Name of nearest known solar system object if exists within 30 arcsec (from MPC archive)",
    )
    ranr: float = Field(
        description="Right Ascension of nearest source in reference image PSF-catalog; J2000 [deg]"
    )
    decnr: float = Field(
        description="Declination of nearest source in reference image PSF-catalog; J2000 [deg]"
    )
    sgmag1: float | None = Field(
        None,
        description="g-band PSF-fit magnitude of closest source from PS1 catalog; if exists within 30 arcsec [mag]",
    )
    srmag1: float | None = Field(
        None,
        description="r-band PSF-fit magnitude of closest source from PS1 catalog; if exists within 30 arcsec [mag]",
    )
    simag1: float | None = Field(
        None,
        description="i-band PSF-fit magnitude of closest source from PS1 catalog; if exists within 30 arcsec [mag]",
    )
    szmag1: float | None = Field(
        None,
        description="z-band PSF-fit magnitude of closest source from PS1 catalog; if exists within 30 arcsec [mag]",
    )
    sgscore1: float | None = Field(
        None,
        description="Star/Galaxy score of closest source from PS1 catalog; if exists within 30 arcsec: 0 <= sgscore <= 1 where closer to 1 implies higher likelihood of being a star",
    )
    distpsnr1: float | None = Field(
        None,
        description="Distance to closest source from PS1 catalog; if exists within 30 arcsec [arcsec]",
    )
    ndethist: int = Field(
        ...,
        ge=0,
        description="Number of spatially-coincident detections falling within 1.5 arcsec going back to beginning of survey",
    )
    ncovhist: int = Field(
        ...,
        ge=0,
        description="Number of times input candidate position fell on any field and readout-channel going back to beginning of survey",
    )
    jdstarthist: float | None = Field(
        None,
        description="Earliest Julian date of epoch corresponding to ndethist [days]",
    )
    scorr: float | None = Field(
        None,
        description="Peak-pixel signal-to-noise ratio in point source matched-filtered detection image",
    )
    sgmag2: float | None = Field(
        None,
        description="g-band PSF-fit magnitude of second closest source from PS1 catalog; if exists within 30 arcsec [mag]",
    )
    srmag2: float | None = Field(
        None,
        description="r-band PSF-fit magnitude of second closest source from PS1 catalog; if exists within 30 arcsec [mag]",
    )
    simag2: float | None = Field(
        None,
        description="i-band PSF-fit magnitude of second closest source from PS1 catalog; if exists within 30 arcsec [mag]",
    )
    szmag2: float | None = Field(
        None,
        description="z-band PSF-fit magnitude of second closest source from PS1 catalog; if exists within 30 arcsec [mag]",
    )
    sgscore2: float | None = Field(
        None,
        description="Star/Galaxy score of second closest source from PS1 catalog; if exists within 30 arcsec: 0 <= sgscore <= 1 where closer to 1 implies higher likelihood of being a star",
    )
    distpsnr2: float | None = Field(
        None,
        description="Distance to second closest source from PS1 catalog; if exists within 30 arcsec [arcsec]",
    )
    sgmag3: float | None = Field(
        None,
        description="g-band PSF-fit magnitude of third closest source from PS1 catalog; if exists within 30 arcsec [mag]",
    )
    srmag3: float | None = Field(
        None,
        description="r-band PSF-fit magnitude of third closest source from PS1 catalog; if exists within 30 arcsec [mag]",
    )
    simag3: float | None = Field(
        None,
        description="i-band PSF-fit magnitude of third closest source from PS1 catalog; if exists within 30 arcsec [mag]",
    )
    szmag3: float | None = Field(
        None,
        description="z-band PSF-fit magnitude of third closest source from PS1 catalog; if exists within 30 arcsec [mag]",
    )
    sgscore3: float | None = Field(
        None,
        description="Star/Galaxy score of third closest source from PS1 catalog; if exists within 30 arcsec: 0 <= sgscore <= 1 where closer to 1 implies higher likelihood of being a star",
    )
    distpsnr3: float | None = Field(
        None,
        description="Distance to third closest source from PS1 catalog; if exists within 30 arcsec [arcsec]",
    )
    nmtchps: int = Field(
        ...,
        ge=0,
        description="Number of source matches from PS1 catalog falling within 30 arcsec",
    )
    dsnrms: float | None = Field(
        None,
        description="Ratio: D/stddev(D) on event position where D = difference image",
    )
    ssnrms: float | None = Field(
        None,
        description="Ratio: S/stddev(S) on event position where S = image of convolution: D (x) PSF(D)",
    )
    dsdiff: float | None = Field(
        None, description="Difference of statistics: dsnrms - ssnrms"
    )
    magzpsci: float | None = Field(
        None,
        description="Magnitude zero point for photometry estimates [mag]",
    )
    magzpsciunc: float | None = Field(
        None,
        description="Magnitude zero point uncertainty (in magzpsci) [mag]",
    )
    magzpscirms: float | None = Field(
        None,
        description="RMS (deviation from average) in all differences between instrumental photometry and matched photometric calibrators from science image processing [mag]",
    )
    zpmed: float | None = Field(
        None,
        description="Magnitude zero point from median of all differences between instrumental photometry and matched photometric calibrators from science image processing [mag]",
    )
    exptime: float | None = Field(
        None, description="Integration time of camera exposure [sec]"
    )
    drb: float | None = Field(
        None,
        description="RealBogus quality score from Deep-Learning-based classifier; range is 0 to 1 where closer to 1 is more reliable",
    )
    clrcoeff: float | None = Field(
        None,
        description="Color coefficient from linear fit from photometric calibration of science image",
    )
    clrcounc: float | None = Field(
        None,
        description="Color coefficient uncertainty from linear fit (corresponding to clrcoeff)",
    )
    neargaia: float | None = Field(
        None,
        description="Distance to closest source from Gaia DR1 catalog irrespective of magnitude; if exists within 90 arcsec [arcsec]",
    )
    maggaia: float | None = Field(
        None,
        description="Gaia (G-band) magnitude of closest source from Gaia DR1 catalog irrespective of magnitude; if exists within 90 arcsec [mag]",
    )
    neargaiabright: float | None = Field(
        None,
        description="Distance to closest source from Gaia DR1 catalog brighter than magnitude 14; if exists within 90 arcsec [arcsec]",
    )
    maggaiabright: float | None = Field(
        None,
        description="Gaia (G-band) magnitude of closest source from Gaia DR1 catalog brighter than magnitude 14; if exists within 90 arcsec [mag]",
    )
    psfFlux: float = Field(description="Flux from PSF-fit photometry [nJy]")
    psfFluxErr: float = Field(
        description="1-sigma uncertainty in psfFlux [nJy]"
    )
    snr_psf: float | None = Field(
        None,
        validation_alias=AliasChoices("snr_psf", "snr"),
        description="Signal-to-noise ratio from PSF-fit photometry",
    )
    apFlux: float | None = Field(
        None, description="Flux from aperture photometry [nJy]"
    )
    apFluxErr: float | None = Field(
        None, description="1-sigma uncertainty in apFlux [nJy]"
    )
    snr_ap: float | None = Field(
        None, description="Signal-to-noise ratio from aperture photometry"
    )
    band: Band = Field(description="Filter band identifier")


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
    def from_alert_photometry(
        cls, photometry: dict[str, Any], survey_zp: float
    ) -> "Photometry":
        validated_photometry = AlertPhotometry.model_validate(photometry)
        psfFlux = validated_photometry.psfFlux or 0.0
        psfFluxErr = validated_photometry.psfFluxErr or 1.0
        magpsf, sigmapsf = flux2mag(
            abs(psfFlux * 1e-9),
            psfFluxErr * 1e-9,
            survey_zp,
        )
        snr = abs(psfFlux) / psfFluxErr if psfFluxErr > 0 else 0
        return cls(
            jd=validated_photometry.jd,
            magpsf=magpsf,
            sigmapsf=sigmapsf,
            isdiffpos=psfFlux > 0,
            psfFlux=validated_photometry.psfFlux,
            psfFluxErr=validated_photometry.psfFluxErr,
            band=validated_photometry.band,
            zp=survey_zp,
            ra=validated_photometry.ra,
            dec=validated_photometry.dec,
            snr=snr,
        )

    @classmethod
    def from_non_detection_photometry(
        cls, photometry: dict[str, Any], survey_zp: float
    ) -> "Photometry":
        validated_photometry = NonDetectionPhotometry.model_validate(
            photometry
        )
        diffmaglim = fluxerr2diffmaglim(
            validated_photometry.psfFluxErr * 1e-9, survey_zp
        )
        return cls(
            jd=validated_photometry.jd,
            magpsf=None,
            sigmapsf=None,
            isdiffpos=None,
            diffmaglim=diffmaglim,
            psfFlux=None,
            psfFluxErr=validated_photometry.psfFluxErr,
            band=validated_photometry.band,
            zp=survey_zp,
            ra=None,
            dec=None,
            snr=None,
        )

    @classmethod
    def from_forced_photometry(
        cls, photometry: dict[str, Any], survey_zp: float
    ) -> "Photometry":
        validated_photometry = ForcedPhotometry.model_validate(photometry)
        psfFlux = validated_photometry.psfFlux or 0.0
        psfFluxErr = validated_photometry.psfFluxErr or 1.0
        snr = abs(psfFlux) / psfFluxErr if psfFluxErr > 0 else 0
        if snr < 3:
            magpsf = None
            sigmapsf = None
            diffmaglim = fluxerr2diffmaglim(psfFluxErr * 1e-9, survey_zp)
        else:
            magpsf, sigmapsf = flux2mag(
                abs(psfFlux * 1e-9),
                psfFluxErr * 1e-9,
                survey_zp,
            )
            diffmaglim = None
        return cls(
            jd=validated_photometry.jd,
            magpsf=magpsf,
            sigmapsf=sigmapsf,
            diffmaglim=diffmaglim,
            psfFlux=validated_photometry.psfFlux,
            psfFluxErr=validated_photometry.psfFluxErr,
            band=validated_photometry.band,
            zp=survey_zp,
            ra=None,
            dec=None,
            snr=snr,
        )

    @property
    def datetime(self) -> Any:  # Returns datetime object from astropy
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
    peak_mag: float | None
    peak_mag_err: float | None
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


class LsstMatch(BaseModel):
    objectId: str = Field(
        ..., validation_alias=AliasChoices("objectId", "object_id")
    )
    ra: float
    dec: float
    prv_candidates: list[Photometry]
    fp_hists: list[Photometry]

    @field_validator("prv_candidates", mode="before")
    @classmethod
    def transform_photometry(cls, v: Any) -> Any:
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
    def transform_forced_photometry(cls, v: Any) -> Any:
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
    candid: int = Field(..., validation_alias=AliasChoices("candid", "_id"))
    objectId: str = Field(
        ..., validation_alias=AliasChoices("objectId", "object_id")
    )
    candidate: ZtfCandidate
    prv_candidates: list[Photometry] | None = None
    prv_nondetections: list[Photometry] | None = None
    fp_hists: list[Photometry] | None = None
    properties: ZtfAlertProperties | None = None
    survey_matches: ZtfSurveyMatches | None = None
    cutoutScience: bytes | None = Field(
        None, validation_alias=AliasChoices("cutoutScience", "cutout_science")
    )
    cutoutTemplate: bytes | None = Field(
        None,
        validation_alias=AliasChoices("cutoutTemplate", "cutout_template"),
    )
    cutoutDifference: bytes | None = Field(
        None,
        validation_alias=AliasChoices("cutoutDifference", "cutout_difference"),
    )

    @field_validator("prv_candidates", mode="before")
    @classmethod
    def transform_photometry(cls, v: Any) -> Any:
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
    """LSST alert candidate data from the LSST alert stream."""

    diaSourceId: int = Field(description="Unique identifier of this DiaSource.")
    visit: int = Field(
        description="Id of the visit where this diaSource was measured."
    )
    detector: int = Field(
        ...,
        ge=0,
        description="Id of the detector where this diaSource was measured.",
    )
    diaObjectId: int | None = Field(
        None,
        description="Id of the diaObject this source was associated with, if any.",
    )
    ssObjectId: int | None = Field(
        None,
        description="Id of the ssObject this source was associated with, if any.",
    )
    parentDiaSourceId: int | None = Field(
        description="Id of the parent diaSource this diaSource has been deblended from, if any."
    )
    midpointMjdTai: float = Field(
        description="Effective mid-visit time for this diaSource, expressed as Modified Julian Date, International Atomic Time."
    )
    ra: float = Field(
        description="Right ascension coordinate of the center of this diaSource."
    )
    raErr: float | None = Field(None, description="Uncertainty of ra.")
    dec: float = Field(
        description="Declination coordinate of the center of this diaSource."
    )
    decErr: float | None = Field(description="Uncertainty of dec.")
    centroid_flag: bool | None = Field(
        description="General centroid algorithm failure flag; set if anything went wrong when fitting the centroid."
    )
    apFlux: float | None = Field(
        description="Flux in a 12 pixel radius aperture on the difference image."
    )
    apFluxErr: float | None = Field(
        description="Estimated uncertainty of apFlux."
    )
    apFlux_flag: bool | None = Field(
        description="General aperture flux algorithm failure flag; set if anything went wrong when measuring aperture fluxes."
    )
    apFlux_flag_apertureTruncated: bool | None = Field(
        description="Aperture did not fit within measurement image."
    )
    psfFlux: float | None = Field(
        description="Flux for Point Source model. Note this actually measures the flux difference between the template and the visit image."
    )
    psfFluxErr: float | None = Field(
        description="Uncertainty of psfFlux."
    )
    psfChi2: float | None = Field(
        description="Chi^2 statistic of the point source model fit."
    )
    psfNdata: int | None = Field(
        description="The number of data points (pixels) used to fit the point source model."
    )
    psfFlux_flag: bool | None = Field(
        description="Failure to derive linear least-squares fit of psf model."
    )
    psfFlux_flag_edge: bool | None = Field(
        description="Object was too close to the edge of the image to use the full PSF model."
    )
    psfFlux_flag_noGoodPixels: bool | None = Field(
        description="Not enough non-rejected pixels in data to attempt the fit."
    )
    trailFlux: float | None = Field(
        description="Flux for a trailed source model. Note this actually measures the flux difference between the template and the visit image."
    )
    trailFluxErr: float | None = Field(
        description="Uncertainty of trailFlux."
    )
    trailRa: float | None = Field(
        description="Right ascension coordinate of centroid for trailed source model."
    )
    trailRaErr: float | None = Field(description="Uncertainty of trailRa.")
    trailDec: float | None = Field(
        description="Declination coordinate of centroid for trailed source model."
    )
    trailDecErr: float | None = Field(description="Uncertainty of trailDec.")
    trailLength: float | None = Field(
        description="Maximum likelihood fit of trail length."
    )
    trailLengthErr: float | None = Field(
        description="Uncertainty of trailLength."
    )
    trailAngle: float | None = Field(
        description="Maximum likelihood fit of the angle between the meridian through the centroid and the trail direction (bearing)."
    )
    trailAngleErr: float | None = Field(
        description="Uncertainty of trailAngle."
    )
    trailChi2: float | None = Field(
        description="Chi^2 statistic of the trailed source model fit."
    )
    trailNdata: int | None = Field(
        description="The number of data points (pixels) used to fit the trailed source model."
    )
    trail_flag_edge: bool | None = Field(
        description="This flag is set if a trailed source extends onto or past edge pixels."
    )
    scienceFlux: float | None = Field(
        description="Forced photometry flux for a point source model measured on the visit image centered at DiaSource position."
    )
    scienceFluxErr: float | None = Field(
        description="Uncertainty of scienceFlux."
    )
    forced_PsfFlux_flag: bool | None = Field(
        description="Forced PSF photometry on science image failed."
    )
    forced_PsfFlux_flag_edge: bool | None = Field(
        description="Forced PSF flux on science image was too close to the edge of the image to use the full PSF model."
    )
    forced_PsfFlux_flag_noGoodPixels: bool | None = Field(
        description="Forced PSF flux not enough non-rejected pixels in data to attempt the fit."
    )
    templateFlux: float | None = Field(
        description="Forced photometry flux for a point source model measured on the template image centered at the DiaObject position."
    )
    templateFluxErr: float | None = Field(
        description="Uncertainty of templateFlux."
    )
    shape_flag: bool | None = Field(
        description="General source shape algorithm failure flag; set if anything went wrong when measuring the shape."
    )
    shape_flag_no_pixels: bool | None = Field(
        description="No pixels to measure shape."
    )
    shape_flag_not_contained: bool | None = Field(
        description="Center not contained in footprint bounding box."
    )
    shape_flag_parent_source: bool | None = Field(
        description="This source is a parent source; we should only be measuring on deblended children in difference imaging."
    )
    extendedness: float | None = Field(
        description="A measure of extendedness, computed by comparing an object's moment-based traced radius to the PSF moments. extendedness = 1 implies a high degree of confidence that the source is extended. extendedness = 0 implies a high degree of confidence that the source is point-like."
    )
    reliability: float | None = Field(
        description="A measure of reliability, computed using information from the source and image characterization, as well as the information on the Telescope and Camera system."
    )
    band: Band | None = Field(
        description="Filter band this source was observed with."
    )
    isDipole: bool | None = Field(
        description="Source well fit by a dipole."
    )
    pixelFlags: bool | None = Field(
        description="General pixel flags failure; set if anything went wrong when setting pixels flags from this footprint's mask."
    )
    pixelFlags_bad: bool | None = Field(
        description="Bad pixel in the DiaSource footprint."
    )
    pixelFlags_cr: bool | None = Field(
        description="Cosmic ray in the DiaSource footprint."
    )
    pixelFlags_crCenter: bool | None = Field(
        description="Cosmic ray in the 3x3 region around the centroid."
    )
    pixelFlags_edge: bool | None = Field(
        description="Some of the source footprint is outside usable exposure region (masked EDGE or centroid off image)."
    )
    pixelFlags_nodata: bool | None = Field(
        description="NO_DATA pixel in the source footprint."
    )
    pixelFlags_nodataCenter: bool | None = Field(
        description="NO_DATA pixel in the 3x3 region around the centroid."
    )
    pixelFlags_interpolated: bool | None = Field(
        description="Interpolated pixel in the DiaSource footprint."
    )
    pixelFlags_interpolatedCenter: bool | None = Field(
        description="Interpolated pixel in the 3x3 region around the centroid."
    )
    pixelFlags_offimage: bool | None = Field(
        description="DiaSource center is off image."
    )
    pixelFlags_saturated: bool | None = Field(
        description="Saturated pixel in the DiaSource footprint."
    )
    pixelFlags_saturatedCenter: bool | None = Field(
        description="Saturated pixel in the 3x3 region around the centroid."
    )
    pixelFlags_suspect: bool | None = Field(
        description="DiaSource's footprint includes suspect pixels."
    )
    pixelFlags_suspectCenter: bool | None = Field(
        description="Suspect pixel in the 3x3 region around the centroid."
    )
    pixelFlags_streak: bool | None = Field(
        description="Streak in the DiaSource footprint."
    )
    pixelFlags_streakCenter: bool | None = Field(
        description="Streak in the 3x3 region around the centroid."
    )
    pixelFlags_injected: bool | None = Field(
        description="Injection in the DiaSource footprint."
    )
    pixelFlags_injectedCenter: bool | None = Field(
        description="Injection in the 3x3 region around the centroid."
    )
    pixelFlags_injected_template: bool | None = Field(
        description="Template injection in the DiaSource footprint."
    )
    pixelFlags_injected_templateCenter: bool | None = Field(
        description="Template injection in the 3x3 region around the centroid."
    )
    glint_trail: bool | None = Field(
        description="This flag is set if the source is part of a glint trail."
    )
    objectId: str = Field(
        ...,
        validation_alias=AliasChoices("objectId", "object_id"),
        description="Object ID for the diaObject or ssObject this source was associated with.",
    )
    jd: float = Field(description="Observation Julian date [days].")
    magpsf: float = Field(
        description="Magnitude from PSF-fit photometry [mag]."
    )
    sigmapsf: float = Field(
        description="1-sigma uncertainty in magpsf [mag]."
    )
    diffmaglim: float = Field(
        description="5-sigma mag limit in difference image [mag]."
    )
    isdiffpos: bool = Field(
        description="True if candidate is from positive (sci minus ref) subtraction."
    )
    snr: float = Field(
        description="Signal-to-noise ratio at which this source was detected in the difference image."
    )
    magap: float = Field(description="Aperture magnitude [mag].")
    sigmagap: float = Field(
        description="1-sigma uncertainty in magap [mag]."
    )
    jdstarthist: float | None = Field(
        None,
        description="Earliest Julian date of epoch in the detection history [days].",
    )
    ndethist: int | None = Field(
        None, description="Number of spatially-coincident detections."
    )
    snr_psf: float | None = Field(
        None,
        description="Signal-to-noise ratio from PSF-fit photometry.",
    )
    snr_ap: float | None = Field(
        None, description="Signal-to-noise ratio from aperture photometry."
    )
    chipsf: float | None = Field(
        None, description="Reduced chi-square for PSF-fit."
    )


class LsstAlertProperties(BaseModel):
    rock: bool
    stationary: bool
    star: bool | None = None
    near_brightstar: bool | None = None
    photstats: PerBandProperties
    multisurvey_photstats: PerBandProperties


class ZtfMatch(BaseModel):
    objectId: str = Field(
        ..., validation_alias=AliasChoices("objectId", "object_id")
    )
    ra: float
    dec: float
    prv_candidates: list[Photometry]
    prv_nondetections: list[Photometry]
    fp_hists: list[Photometry]

    @field_validator("prv_candidates", mode="before")
    @classmethod
    def transform_photometry(cls, v: Any) -> Any:
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
    def transform_non_detections(cls, v: Any) -> Any:
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
    def transform_forced_photometry(cls, v: Any) -> Any:
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
    candid: int = Field(..., validation_alias=AliasChoices("candid", "_id"))
    objectId: str = Field(
        ..., validation_alias=AliasChoices("objectId", "object_id")
    )
    candidate: LsstCandidate
    prv_candidates: list[Photometry] | None = None
    fp_hists: list[Photometry] | None = None
    properties: LsstAlertProperties | None = None
    cutoutScience: bytes | None = Field(
        None, validation_alias=AliasChoices("cutoutScience", "cutout_science")
    )
    cutoutTemplate: bytes | None = Field(
        None,
        validation_alias=AliasChoices("cutoutTemplate", "cutout_template"),
    )
    cutoutDifference: bytes | None = Field(
        None,
        validation_alias=AliasChoices("cutoutDifference", "cutout_difference"),
    )
    survey_matches: LsstSurveyMatches | None = None

    @field_validator("prv_candidates", mode="before")
    @classmethod
    def transform_photometry(cls, v: Any) -> Any:
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
    def transform_forced_photometry(cls, v: Any) -> Any:
        """Transform ForcedPhotometry dicts to Photometry instances."""
        if isinstance(v, list):
            return [
                Photometry.from_forced_photometry(item, LSST_ZP)
                if isinstance(item, dict)
                else item
                for item in v
            ]
        return v
