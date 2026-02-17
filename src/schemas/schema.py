from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator

class ToolRequestModel(BaseModel):
    stock: str = Field(
        ...,
        description = "정보를 조회하고자 하는 종목의 이름",
        examples = ["삼성전자"]
    )
    market: Literal["코스피", "코스닥", "코넥스", "알수없음"] = Field(
        default = "알수없음",
        description = "정보를 조회하고자 하는 종목이 속한 주식 시장",
        examples = ["코스피"]
    )
    date: Optional[str] = Field(
        default = None,
        description = "정보 조회의 기준이 되는 날짜 (YYYYMMDD)",
        examples = ["20250103"]
    )

    @field_validator("date")
    @classmethod
    def validate_date(cls, date):
        if date is None:
            return date
        try:
            datetime.strptime(date, "%Y%m%d")
        except ValueError:
            raise ValueError("'date' must be in YYYYMMDD format")
        return date
    

class StockInfoOutputModel(BaseModel):
    isu_cd: Optional[str] = Field(
        default=None,
        descrption="표준코드",
        examples=["KR7338100001"],
        alias="ISU_CD"
    )
    isu_srt_cd: Optional[str] = Field(
        default=None,
        descrption="단축코드",
        examples=["338100"],
        alias="ISU_SRT_CD" 
    )
    isu_nm: Optional[str] = Field(
        default=None,
        description="한글 종목명",
        examples=["NH프라임리츠보통주"],
        alias="ISU_NM"
    )
    isu_abbrv: Optional[str] = Field(
        default=None,
        description="한글 종목약명",
        examples=["NH프라임리츠"],
        alias="ISU_ABBRV"
    )
    isu_eng_nm: Optional[str] = Field(
        default=None,
        description="영문 종목명",
        examples=["NH Prime REIT"],
        alias="ISU_ENG_NM"
    )
    list_dd: Optional[str] = Field(
        default=None,
        description="상장일",
        examples=["20191205"],
        alias="LIST_DD"
    )
    mkt_tp_nm: Optional[str] = Field(
        default=None,
        description="시장구분",
        examples=["KOSPI"],
        alias="MKT_TP_NM"
    )
    secugrp_nm: Optional[str] = Field(
        default=None,
        description="증권구분",
        examples=["부동산투자회사"],
        alias="SECUGRP_NM"
    )
    sect_tp_nm: Optional[str] = Field(
        default=None,
        description="소속부",
        examples=["-"],
        alias="SECT_TP_NM"
    )
    kind_stkcert_tp_nm: Optional[str] = Field(
        default=None,
        description="주식종류",
        examples=["보통주"],
        alias="KIND_STKCERT_TP_NM"
    )
    parval: Optional[str] = Field(
        default=None,
        description="액면가",
        examples=["500"],
        alias="PARVAL"
    )
    list_shrs: Optional[str] = Field(
        default=None,
        description="상장주식수",
        examples=["18660000"],
        alias="LIST_SHRS"
    )

    model_config = {
        "extra": "forbid"
    }


class StockPriceOutputModel(BaseModel):
    bas_dd: Optional[str] = Field(
        default=None,
        descrption="기준일자",
        examples=["20200414"],
        alias="BAS_DD"
    )
    isu_cd: Optional[str] = Field(
        default=None,
        descrption="종목코드",
        examples=["338100"],
        alias="ISU_CD"
    )
    isu_nm: Optional[str] = Field(
        default=None,
        description="한글 종목명",
        examples=["NH프라임리츠"],
        alias="ISU_NM"
    )
    mkt_nm: Optional[str] = Field(
        default=None,
        description="시장구분",
        examples=["KOSPI"],
        alias="MKT_NM"
    )
    sect_tp_nm: Optional[str] = Field(
        default=None,
        description="소속부",
        examples=["-"],
        alias="SECT_TP_NM"
    )
    tdd_clsprc: Optional[str] = Field(
        default=None,
        description="종가",
        examples=["4715"],
        alias="TDD_CLSPRC"
    )
    cmpprevdd_prc: Optional[str] = Field(
        default=None,
        description="대비",
        examples=["25"],
        alias="CMPPREVDD_PRC"
    )
    fluc_rt: Optional[str] = Field(
        default=None,
        description="등락률",
        examples=["0.53"],
        alias="FLUC_RT"
    )
    tdd_opnprc: Optional[str] = Field(
        default=None,
        description="시가",
        examples=["4655"],
        alias="TDD_OPNPRC"
    )
    tdd_hgprc: Optional[str] = Field(
        default=None,
        description="고가",
        examples=["4720"],
        alias="TDD_HGPRC"
    )
    tdd_lwprc: Optional[str] = Field(
        default=None,
        description="저가",
        examples=["4655"],
        alias="TDD_LWPRC"
    )
    acc_trdvol: Optional[str] = Field(
        default=None,
        description="거래량",
        examples=["21363"],
        alias="ACC_TRDVOL"
    )
    acc_trdval: Optional[str] = Field(
        default=None,
        description="거래대금",
        examples=["100332885"],
        alias="ACC_TRDVAL"
    )
    mktcap: Optional[str] = Field(
        default=None,
        description="시가총액",
        examples=["87981900000"],
        alias="MKTCAP"
    )
    list_shrs: Optional[str] = Field(
        default=None,
        description="시가총액",
        examples=["18660000"],
        alias="LIST_SHRS"
    )

    model_config = {
        "extra": "forbid"
    }