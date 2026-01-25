"""Pydantic raw models for ZTF and LSST alerts, generated from avro schemas."""
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Band(str, Enum):
    g = "g"
    r = "r"
    i = "i"
    z = "z"
    y = "y"
    u = "u"


class ZtfCandidate(BaseModel):
    jd: float
    fid: int = Field(..., ge=-2**31, le=(2**31 - 1))
    pid: int
    diffmaglim: Optional[float]
    programpi: Optional[str]
    programid: int = Field(..., ge=-2**31, le=(2**31 - 1))
    candid: int
    isdiffpos: bool
    nid: Optional[int]
    rcid: Optional[int]
    field: Optional[int]
    ra: float
    dec: float
    magpsf: float
    sigmapsf: float
    chipsf: Optional[float]
    magap: Optional[float]
    sigmagap: Optional[float]
    distnr: Optional[float]
    magnr: Optional[float]
    sigmagnr: Optional[float]
    chinr: Optional[float]
    sharpnr: Optional[float]
    sky: Optional[float]
    fwhm: Optional[float]
    classtar: Optional[float]
    mindtoedge: Optional[float]
    seeratio: Optional[float]
    aimage: Optional[float]
    bimage: Optional[float]
    elong: Optional[float]
    nneg: Optional[int]
    nbad: Optional[int]
    rb: Optional[float]
    ssdistnr: Optional[float]
    ssmagnr: Optional[float]
    ssnamenr: Optional[str]
    ranr: float
    decnr: float
    sgmag1: Optional[float]
    srmag1: Optional[float]
    simag1: Optional[float]
    szmag1: Optional[float]
    sgscore1: Optional[float]
    distpsnr1: Optional[float]
    ndethist: int = Field(..., ge=-2**31, le=(2**31 - 1))
    ncovhist: int = Field(..., ge=-2**31, le=(2**31 - 1))
    jdstarthist: Optional[float]
    scorr: Optional[float]
    sgmag2: Optional[float]
    srmag2: Optional[float]
    simag2: Optional[float]
    szmag2: Optional[float]
    sgscore2: Optional[float]
    distpsnr2: Optional[float]
    sgmag3: Optional[float]
    srmag3: Optional[float]
    simag3: Optional[float]
    szmag3: Optional[float]
    sgscore3: Optional[float]
    distpsnr3: Optional[float]
    nmtchps: int = Field(..., ge=-2**31, le=(2**31 - 1))
    dsnrms: Optional[float]
    ssnrms: Optional[float]
    dsdiff: Optional[float]
    magzpsci: Optional[float]
    magzpsciunc: Optional[float]
    magzpscirms: Optional[float]
    zpmed: Optional[float]
    exptime: Optional[float]
    drb: Optional[float]
    clrcoeff: Optional[float]
    clrcounc: Optional[float]
    neargaia: Optional[float]
    maggaia: Optional[float]
    neargaiabright: Optional[float]
    maggaiabright: Optional[float]
    psfFlux: float
    psfFluxErr: float
    snr: float
    band: Band


class ZtfPhotometry(BaseModel):
    jd: float
    magpsf: Optional[float]
    sigmapsf: Optional[float]
    diffmaglim: float
    psfFlux: Optional[float]
    psfFluxErr: float
    band: Band
    zp: Optional[float]
    ra: Optional[float]
    dec: Optional[float]
    snr: Optional[float]
    programid: int = Field(..., ge=-2**31, le=(2**31 - 1))


class BandRateProperties(BaseModel):
    rate: float
    rate_error: float
    red_chi2: float
    nb_data: int = Field(..., ge=-2**31, le=(2**31 - 1))
    dt: float


class BandProperties(BaseModel):
    peak_jd: float
    peak_mag: float
    peak_mag_err: float
    dt: float
    rising: Optional[BandRateProperties]
    fading: Optional[BandRateProperties]


class PerBandProperties(BaseModel):
    g: Optional[BandProperties]
    r: Optional[BandProperties]
    i: Optional[BandProperties]
    z: Optional[BandProperties]
    y: Optional[BandProperties]
    u: Optional[BandProperties]


class ZtfAlertProperties(BaseModel):
    rock: bool
    star: bool
    near_brightstar: bool
    stationary: bool
    photstats: PerBandProperties
    multisurvey_photstats: Optional[PerBandProperties]


class LsstPhotometry(BaseModel):
    jd: float
    magpsf: Optional[float]
    sigmapsf: Optional[float]
    diffmaglim: float
    psfFlux: Optional[float]
    psfFluxErr: float
    band: Band
    zp: Optional[float]
    ra: Optional[float]
    dec: Optional[float]
    snr: Optional[float]


class LsstMatch(BaseModel):
    object_id: str
    ra: float
    dec: float
    prv_candidates: List[LsstPhotometry]
    fp_hists: List[LsstPhotometry]


class ZtfSurveyMatches(BaseModel):
    lsst: Optional[LsstMatch]


class EnrichedZtfAlert(BaseModel):
    candid: int
    objectId: str
    candidate: ZtfCandidate
    prv_candidates: List[ZtfPhotometry]
    prv_nondetections: List[ZtfPhotometry]
    fp_hists: List[ZtfPhotometry]
    properties: ZtfAlertProperties
    survey_matches: Optional[ZtfSurveyMatches]
    cutoutScience: Optional[bytes]
    cutoutTemplate: Optional[bytes]
    cutoutDifference: Optional[bytes]


class LsstCandidate(BaseModel):
    diaSourceId: int
    visit: int
    detector: int = Field(..., ge=-2**31, le=(2**31 - 1))
    diaObjectId: Optional[int]
    ssObjectId: Optional[int]
    parentDiaSourceId: Optional[int]
    midpointMjdTai: float
    ra: float
    raErr: Optional[float]
    dec: float
    decErr: Optional[float]
    centroid_flag: Optional[bool]
    apFlux: Optional[float]
    apFluxErr: Optional[float]
    apFlux_flag: Optional[bool]
    apFlux_flag_apertureTruncated: Optional[bool]
    psfFlux: Optional[float]
    psfFluxErr: Optional[float]
    psfChi2: Optional[float]
    psfNdata: Optional[int]
    psfFlux_flag: Optional[bool]
    psfFlux_flag_edge: Optional[bool]
    psfFlux_flag_noGoodPixels: Optional[bool]
    trailFlux: Optional[float]
    trailFluxErr: Optional[float]
    trailRa: Optional[float]
    trailRaErr: Optional[float]
    trailDec: Optional[float]
    trailDecErr: Optional[float]
    trailLength: Optional[float]
    trailLengthErr: Optional[float]
    trailAngle: Optional[float]
    trailAngleErr: Optional[float]
    trailChi2: Optional[float]
    trailNdata: Optional[int]
    trail_flag_edge: Optional[bool]
    scienceFlux: Optional[float]
    scienceFluxErr: Optional[float]
    forced_PsfFlux_flag: Optional[bool]
    forced_PsfFlux_flag_edge: Optional[bool]
    forced_PsfFlux_flag_noGoodPixels: Optional[bool]
    templateFlux: Optional[float]
    templateFluxErr: Optional[float]
    shape_flag: Optional[bool]
    shape_flag_no_pixels: Optional[bool]
    shape_flag_not_contained: Optional[bool]
    shape_flag_parent_source: Optional[bool]
    extendedness: Optional[float]
    reliability: Optional[float]
    band: Optional[Band]
    isDipole: Optional[bool]
    pixelFlags: Optional[bool]
    pixelFlags_bad: Optional[bool]
    pixelFlags_cr: Optional[bool]
    pixelFlags_crCenter: Optional[bool]
    pixelFlags_edge: Optional[bool]
    pixelFlags_nodata: Optional[bool]
    pixelFlags_nodataCenter: Optional[bool]
    pixelFlags_interpolated: Optional[bool]
    pixelFlags_interpolatedCenter: Optional[bool]
    pixelFlags_offimage: Optional[bool]
    pixelFlags_saturated: Optional[bool]
    pixelFlags_saturatedCenter: Optional[bool]
    pixelFlags_suspect: Optional[bool]
    pixelFlags_suspectCenter: Optional[bool]
    pixelFlags_streak: Optional[bool]
    pixelFlags_streakCenter: Optional[bool]
    pixelFlags_injected: Optional[bool]
    pixelFlags_injectedCenter: Optional[bool]
    pixelFlags_injected_template: Optional[bool]
    pixelFlags_injected_templateCenter: Optional[bool]
    glint_trail: Optional[bool]
    objectId: str
    jd: float
    magpsf: float
    sigmapsf: float
    diffmaglim: float
    isdiffpos: bool
    snr: float
    magap: float
    sigmagap: float
    jdstarthist: Optional[float]
    ndethist: Optional[int]


class LsstAlertProperties(BaseModel):
    rock: bool
    stationary: bool
    star: Optional[bool]
    photstats: PerBandProperties
    multisurvey_photstats: PerBandProperties


class ZtfMatch(BaseModel):
    object_id: str
    ra: float
    dec: float
    prv_candidates: List[ZtfPhotometry]
    prv_nondetections: List[ZtfPhotometry]
    fp_hists: List[ZtfPhotometry]


class LsstSurveyMatches(BaseModel):
    ztf: Optional[ZtfMatch]


class EnrichedLsstAlert(BaseModel):
    candid: int
    objectId: str
    candidate: LsstCandidate
    prv_candidates: List[LsstPhotometry]
    fp_hists: List[LsstPhotometry]
    properties: LsstAlertProperties
    cutoutScience: Optional[bytes]
    cutoutTemplate: Optional[bytes]
    cutoutDifference: Optional[bytes]
    survey_matches: Optional[LsstSurveyMatches]
