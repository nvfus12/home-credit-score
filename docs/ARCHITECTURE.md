# Kiến Trúc Hệ Thống (System Architecture & Design Decisions)

Tài liệu này chi tiết các quyết định thiết kế kiến trúc và mô hình hóa trong dự án **CreditLens AI**.

---

## 1. Nguyên Tắc Thiết Kế Sạch (Clean Architecture)

Dự án áp dụng cấu trúc phân tầng rõ ràng để đảm bảo tính độc lập và khả năng bảo trì lâu dài của hệ thống:

```
[Presentation / Frontend]
          │ (REST API / HTML / CSS / JS)
          ▼
   [Application Layers] ◄───► [Business Rules / Services]
    (FastAPI / Schemas)       (CreditScorer / Explainer / Classifier)
          │                              │
          ▼                              ▼
[Infrastructure / DB]        [ML Artifacts & Pipelines]
(SQLAlchemy / SQLite)        (XGBoost / TreeSHAP / Preprocessing)
```

### Các tầng kiến trúc chính:
1.  **Domain Business Logic (`app/services/`):** Chứa các quy tắc nghiệp vụ cốt lõi không phụ thuộc vào framework. Ví dụ: cách tính toán Credit Score từ xác suất (`risk_classifier.py`), cách tính giá trị SHAP (`explainer.py`).
2.  **Application Layer (`app/api/` & `app/schemas/`):** Nhận đầu vào, thực thi xác thực schema bằng Pydantic và điều phối các service nghiệp vụ để trả về kết quả cho client.
3.  **Data & Infrastructure Layer (`app/database/`):** Thực hiện kết nối cơ sở dữ liệu SQLite bất đồng bộ bằng SQLAlchemy Async Engine để ghi chép log suy luận (inference logs) mà không gây chặn luồng xử lý API.
4.  **Offline ML Pipeline (`ml/`):** Tách biệt hoàn toàn luồng huấn luyện mô hình (Offline training) và luồng suy luận trực tuyến (Online inference). Điều này đảm bảo code chạy trực tuyến không bị phình to bởi các logic phân tích dữ liệu cồng kềnh.

---

## 2. Thiết Kế ML Pipeline & Mô Hình Hóa

### Thuật toán lựa chọn: XGBoost (eXtreme Gradient Boosting)
*   **Lý do:** Đối với dữ liệu dạng bảng có nhiều giá trị khuyết và phân phối lệch, XGBoost vượt trội hơn hẳn Neural Networks về cả độ chính xác (ROC-AUC) và tốc độ huấn luyện.
*   **Xử lý mất cân bằng nhãn (Class Imbalance):** Tỷ lệ nợ xấu trong dữ liệu tài chính thường chỉ khoảng 8%. Dự án tính toán động tỷ lệ âm/dương nhãn và đưa vào tham số `scale_pos_weight` của XGBoost để tối ưu hóa trực tiếp hàm mất mát cho lớp thiểu số (Default clients).
*   **Hyperparameter Tuning:** Sử dụng thư viện **Optuna** chạy trên GPU của Kaggle Notebooks. Optuna tìm kiếm tự động các siêu tham số trong không gian 7 chiều (số cây, độ sâu, tỷ lệ lấy mẫu con, tốc độ học...) giúp nâng cao ROC-AUC trên tập Validation lên mức tối đa.

---

## 3. Explainable AI (XAI) & TreeSHAP

Mô hình tín dụng tài chính bắt buộc phải giải thích được để tuân thủ pháp lý (Regulatory Compliance) và giúp nhân viên thẩm định (Credit Officer) hiểu rõ rủi ro của từng khách hàng.

*   **TreeSHAP (Shapley Additive exPlanations):** Dự án sử dụng TreeSHAP được tích hợp sẵn cho mô hình cây của XGBoost. Thuật toán này tính toán chính xác mức độ đóng góp của từng đặc trưng (features) tới kết quả dự đoán của mô hình dưới dạng toán học chặt chẽ.
*   **Online Latency Optimization:** Vì tính toán SHAP khá tốn CPU, hệ thống được tối ưu hóa chỉ tính toán trên 1 dòng dữ liệu yêu cầu hiện tại (Local Explanation) thay vì toàn bộ tập dữ liệu, giúp thời gian phản hồi của API duy trì dưới **200ms**.
*   **Visual Integration:** Biểu đồ SHAP được sinh dưới dạng ảnh PNG có màu nền trong suốt, khớp hoàn toàn với giao diện tối (Dark Theme) của ứng dụng web, tránh việc chèn ảnh nền trắng thô sơ thường thấy ở các ứng dụng prototype.

---

## 4. MLOps Giám Sát Độ Lệch Dữ Liệu (Data Drift)

Trong tài chính, sự thay đổi của nền kinh tế (Concept Drift) hoặc thay đổi tệp khách hàng mục tiêu (Data Drift) là nguyên nhân chính khiến mô hình bị giảm độ chính xác theo thời gian.

*   **Inference Logging:** Mỗi yêu cầu chấm điểm tín dụng thành công sẽ được ghi lại đầy đủ các thuộc tính đầu vào và đầu ra vào bảng `inference_logs`.
*   **Evidently AI Integration:** Tích hợp bộ công cụ giám sát Evidently AI. Khi người dùng truy cập tab Giám sát, hệ thống sẽ tự động truy vấn toàn bộ dữ liệu log thực tế trong cơ sở dữ liệu và so sánh phân phối thống kê với tập dữ liệu huấn luyện chuẩn (`reference_data.parquet`).
*   **Chỉ số PSI (Population Stability Index):** PSI được sử dụng để định lượng mức độ lệch dữ liệu. 
    *   $PSI < 0.1$: Dữ liệu ổn định.
    *   $0.1 \le PSI \le 0.25$: Phát hiện sự lệch nhẹ, cần theo dõi.
    *   $PSI > 0.25$: Lệch dữ liệu nghiêm trọng (Drifted), hệ thống sẽ phát cảnh báo màu đỏ khuyên nghị kỹ sư AI tiến hành thu thập thêm mẫu mới và retrain mô hình.
