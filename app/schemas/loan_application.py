from pydantic import BaseModel, Field
from typing import Optional

class LoanApplication(BaseModel):
    applicant_age: float = Field(..., ge=18, le=100, description="Tuổi khách hàng (năm)")
    income_total: float = Field(..., ge=0, description="Thu nhập tổng hàng tháng (VND hoặc USD)")
    employment_years: float = Field(..., ge=0, le=80, description="Số năm kinh nghiệm làm việc")
    loan_amount: float = Field(..., ge=0, description="Số tiền khoản vay yêu cầu")
    loan_annuity: float = Field(..., ge=0, description="Số tiền trả góp hàng năm/tháng")
    goods_price: float = Field(..., ge=0, description="Giá trị tài sản thế chấp/hàng hóa mua")
    num_children: int = Field(default=0, ge=0, description="Số con cái")
    education_type: str = Field(default="Higher education", description="Trình độ học vấn")
    housing_type: str = Field(default="House / apartment", description="Hình thức cư trú")
    bureau_loans_active: int = Field(default=0, ge=0, description="Số khoản vay hiện đang hoạt động ở tổ chức khác (CIC)")
    bureau_overdue_count: int = Field(default=0, ge=0, description="Số khoản nợ quá hạn ở tổ chức khác")
    prev_application_count: int = Field(default=0, ge=0, description="Số lần nộp đơn vay trong quá khứ tại Home Credit")
    prev_approved_ratio: float = Field(default=0.0, ge=0.0, le=1.0, description="Tỷ lệ hồ sơ được duyệt trong quá khứ")
    external_source_1: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Điểm tín nhiệm từ đối tác bên thứ nhất")
    external_source_2: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Điểm tín nhiệm từ đối tác bên thứ hai")
    external_source_3: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Điểm tín nhiệm từ đối tác bên thứ ba")

    class Config:
        json_schema_extra = {
            "example": {
                "applicant_age": 35.5,
                "income_total": 45000000,
                "employment_years": 8.0,
                "loan_amount": 250000000,
                "loan_annuity": 15000000,
                "goods_price": 230000000,
                "num_children": 1,
                "education_type": "Higher education",
                "housing_type": "House / apartment",
                "bureau_loans_active": 2,
                "bureau_overdue_count": 0,
                "prev_application_count": 3,
                "prev_approved_ratio": 0.67,
                "external_source_1": 0.55,
                "external_source_2": 0.62,
                "external_source_3": 0.48
            }
        }
        extra = "ignore"
