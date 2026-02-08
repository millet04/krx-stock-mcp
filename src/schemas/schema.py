from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator

class ToolRequestModel(BaseModel):
    stock: str = Field(
        description = "정보를 조회하고자 하는 종목의 이름",
        example = "삼성전자",
    )
    market: Literal["코스피", "코스닥", "코넥스", "알수없음"] = Field(
        default = "알수없음",
        description = "정보를 조회하고자 하는 종목이 속한 주식 시장",
        example = "코스피"
    )
    date: Optional[str] = Field(
        default = None,
        description = "정보 조회의 기준이 되는 날짜 (YYYYMMDD)",
        example = "20250103"
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