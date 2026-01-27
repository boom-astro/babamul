"""Pydantic raw models for ZTF and LSST alerts, generated from avro schemas."""

from enum import Enum

from pydantic import AliasChoices, BaseModel, Field


class Band(str, Enum):
    g = "g"
    r = "r"
    i = "i"
    z = "z"
    y = "y"
    u = "u"


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
    ssnamenr: str | None
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
    jdstarthist: float | None
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


class ZtfPhotometry(BaseModel):
    jd: float
    magpsf: float | None
    sigmapsf: float | None
    diffmaglim: float
    psfFlux: float | None
    psfFluxErr: float
    band: Band
    zp: float | None
    ra: float | None
    dec: float | None
    snr: float | None
    programid: int = Field(..., ge=-(2**31), le=(2**31 - 1))


class BandRateProperties(BaseModel):
    rate: float
    rate_error: float
    red_chi2: float
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


class LsstPhotometry(BaseModel):
    jd: float
    magpsf: float | None
    sigmapsf: float | None
    diffmaglim: float
    psfFlux: float | None
    psfFluxErr: float
    band: Band
    zp: float | None
    ra: float | None
    dec: float | None
    snr: float | None


class LsstMatch(BaseModel):
    objectId: str = Field(..., alias=AliasChoices("objectId", "object_id"))
    ra: float
    dec: float
    prv_candidates: list[LsstPhotometry]
    fp_hists: list[LsstPhotometry]


class ZtfSurveyMatches(BaseModel):
    lsst: LsstMatch | None


class EnrichedZtfAlert(BaseModel):
    candid: int = Field(..., alias=AliasChoices("candid", "_id"))
    objectId: str = Field(..., alias=AliasChoices("objectId", "object_id"))
    candidate: ZtfCandidate
    prv_candidates: list[ZtfPhotometry]
    prv_nondetections: list[ZtfPhotometry]
    fp_hists: list[ZtfPhotometry]
    properties: ZtfAlertProperties
    survey_matches: ZtfSurveyMatches | None
    cutoutScience: bytes | None = Field(
        None, alias=AliasChoices("cutoutScience", "cutout_science")
    )
    cutoutTemplate: bytes | None = Field(
        None, alias=AliasChoices("cutoutTemplate", "cutout_template")
    )
    cutoutDifference: bytes | None = Field(
        None, alias=AliasChoices("cutoutDifference", "cutout_difference")
    )


class LsstCandidate(BaseModel):
    diaSourceId: int
    visit: int
    detector: int = Field(..., ge=-(2**31), le=(2**31 - 1))
    diaObjectId: int | None
    ssObjectId: int | None
    parentDiaSourceId: int | None
    midpointMjdTai: float
    ra: float
    raErr: float | None
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
    jdstarthist: float | None
    ndethist: int | None


class LsstAlertProperties(BaseModel):
    rock: bool
    stationary: bool
    star: bool | None
    photstats: PerBandProperties
    multisurvey_photstats: PerBandProperties


class ZtfMatch(BaseModel):
    objectId: str = Field(..., alias=AliasChoices("objectId", "object_id"))
    ra: float
    dec: float
    prv_candidates: list[ZtfPhotometry]
    prv_nondetections: list[ZtfPhotometry]
    fp_hists: list[ZtfPhotometry]


class LsstSurveyMatches(BaseModel):
    ztf: ZtfMatch | None


class EnrichedLsstAlert(BaseModel):
    candid: int = Field(..., alias=AliasChoices("candid", "_id"))
    objectId: str = Field(..., alias=AliasChoices("objectId", "object_id"))
    candidate: LsstCandidate
    prv_candidates: list[LsstPhotometry]
    fp_hists: list[LsstPhotometry]
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
    survey_matches: LsstSurveyMatches | None
