# Tài Liệu API (API Reference Documentation)

Ứng dụng CreditLens AI cung cấp các API RESTful phiên bản `v1` để tích hợp dịch vụ chấm điểm tín dụng và giám sát MLOps.

---

## 1. API Chấm Điểm Tín Dụng (Credit Scoring)

### `POST /api/v1/predict`
Thực hiện đánh giá rủi ro tín dụng của khách hàng dựa trên thông tin hồ sơ và tính toán biểu đồ SHAP giải thích.

**Đầu vào (Request Body - JSON):**
```json
{
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
  "external_source_2": 0.55,
  "external_source_3": 0.48
}
```

**Đầu ra (Response Body - JSON):**
```json
{
  "prediction_id": "pred_a1b2c3d4",
  "timestamp": "2026-06-29T17:10:00.123456Z",
  "default_probability": 0.125,
  "credit_score": 781,
  "risk_grade": "Good",
  "risk_color": "#3b82f6",
  "recommended_action": "APPROVE_WITH_CONDITIONS",
  "action_description": "Khách hàng có lịch sử tín dụng khá. Đề xuất duyệt vay kèm các điều khoản/giám sát bổ sung.",
  "explanation": {
    "shap_plot_url": "/static/assets/shap_plots/pred_a1b2c3d4.png",
    "top_risk_factors": [
      {
        "feature": "bureau_overdue_count",
        "display_name": "Số khoản nợ CIC quá hạn",
        "shap_value": 0.082,
        "direction": "risk_increase",
        "description": "Chỉ số Số khoản CIC nợ quá hạn tăng thêm nguy cơ nợ xấu (+8.2% log-odds)."
      }
    ],
    "total_features_analyzed": 21
  }
}
```

**Mã trạng thái phản hồi:**
*   `200 OK`: Chấm điểm thành công.
*   `400 Bad Request`: Định dạng dữ liệu đầu vào không hợp lệ (ví dụ: tuổi dưới 18, số tiền âm).
*   `503 Service Unavailable`: Dịch vụ chưa sẵn sàng (Mô hình chưa được huấn luyện hoặc bị thiếu file).

---

## 2. API Lịch Sử Thẩm Định (Audit Trail)

### `GET /api/v1/predictions/history`
Lấy danh sách các hồ sơ tín dụng đã được thẩm định tự động, hỗ trợ phân trang và lọc theo mức rủi ro.

**Tham số truy vấn (Query Parameters):**
*   `page` (int, default=1): Trang hiện tại.
*   `limit` (int, default=20, max=100): Số bản ghi trên mỗi trang.
*   `risk_grade` (str, optional): Bộ lọc theo hạng rủi ro (`Excellent`, `Good`, `Fair`, `Poor`).

**Đầu ra (Response Body - JSON):**
```json
{
  "page": 1,
  "limit": 10,
  "total_records": 150,
  "items": [
    {
      "prediction_id": "pred_a1b2c3d4",
      "timestamp": "2026-06-29T17:10:00.123456Z",
      "applicant_name": "Khách hàng c3d4",
      "applicant_age": 35.5,
      "income_total": 45000000,
      "loan_amount": 250000000,
      "default_probability": 0.125,
      "credit_score": 781,
      "risk_grade": "Good",
      "recommended_action": "APPROVE_WITH_CONDITIONS",
      "shap_plot_url": "/static/assets/shap_plots/pred_a1b2c3d4.png"
    }
  ]
}
```

---

## 3. API Giám Sát MLOps (Monitoring)

### `GET /api/v1/monitoring/stats`
Trả về các số liệu thống kê nhanh về hệ thống chấm điểm phục vụ Dashboard giám sát.

**Đầu ra (Response Body - JSON):**
```json
{
  "total_predictions": 1250,
  "today_predictions": 45,
  "avg_default_probability": 0.115,
  "risk_distribution": {
    "Excellent": 300,
    "Good": 650,
    "Fair": 200,
    "Poor": 100
  },
  "model_version": "v1.0.0",
  "model_trained_at": "2026-06-15T10:00:00Z",
  "system_health": "OK",
  "active_alerts": []
}
```

### `GET /api/v1/monitoring/drift-report`
Tính toán độ lệch dữ liệu và sinh báo cáo HTML của Evidently AI.

**Đầu ra (Response Body - JSON):**
```json
{
  "report_generated_at": "2026-06-29T17:15:00Z",
  "total_predictions_since_deploy": 1250,
  "dataset_drift_detected": false,
  "drift_share": 0.05,
  "drifted_features": [
    {
      "feature": "income_total",
      "psi": 0.045,
      "status": "STABLE",
      "alert": "OK"
    }
  ],
  "target_drift": {
    "predicted_default_rate_reference": 0.082,
    "predicted_default_rate_current": 0.091,
    "status": "STABLE"
  },
  "evidently_html_report_url": "/static/assets/drift_reports/latest_drift_report.html",
  "recommendation": "Hệ thống hoạt động ổn định. Phân phối dữ liệu thực tế khớp tốt với dữ liệu huấn luyện."
}
```
