---
name: ml_fintech_guidelines
description: Guidelines for financial modeling, time-series validation, handling class imbalance, explainable AI, and MLOps monitoring in Fintech projects.
---

# Quy Tắc Huấn Luyện & Vận Hành Mô Hỏi Tài Chính (Fintech ML & MLOps Guidelines)

Tài liệu này cung cấp các nguyên tắc cốt lõi khi phát triển các hệ thống AI trong lĩnh vực Fintech (như Credit Scoring, Fraud Detection, Portfolio Optimization) để đảm bảo mô hình chạy chính xác, minh bạch và không bị suy giảm hiệu năng trong thực tế.

## 1. Phòng Tránh Rò Rỉ Dữ Liệu (Data Leakage & Lookahead Bias)

Dữ liệu tài chính thường là dữ liệu chuỗi thời gian (time-series). Lỗi phổ biến nhất là sử dụng thông tin từ tương lai để dự đoán quá khứ.

- **Nguyên tắc chia dữ liệu:** 
  - KHÔNG sử dụng `train_test_split` ngẫu nhiên của sklearn đối với dữ liệu có yếu tố thời gian.
  - PHẢI sử dụng chia dữ liệu theo thời gian (Time-based Split) hoặc `TimeSeriesSplit` để đảm bảo dữ liệu Test luôn nằm sau dữ liệu Train về mặt thời gian.
- **Kỹ nghệ đặc trưng (Feature Engineering):**
  - Khi tính toán các chỉ số thống kê trượt (Rolling/Moving Features như trung bình 30 ngày), đảm bảo các chỉ số này chỉ được tính từ thời điểm $t$ trở về trước.
  - Fit các bộ chuyển đổi dữ liệu (như `StandardScaler`, `MinMaxScaler`, `TargetEncoder`) CHỈ trên tập Train, sau đó dùng chung tham số đó để `transform` tập Validation và Test. Không bao giờ được `fit_transform` trên toàn bộ bộ dữ liệu.

## 2. Xử Lý Mất Cân Bằng Dữ Liệu (Imbalanced Data)

Các bài toán như phát hiện gian lận giao dịch hay nợ xấu thường có tỷ lệ nhãn rất lệch (Imbalance Ratio từ 1:100 đến 1:1000).

- **Lựa chọn Metric:**
  - KHÔNG sử dụng `Accuracy` để đánh giá mô hình.
  - PHẢI sử dụng: **Precision-Recall AUC (PR-AUC)**, **F1-Score**, **ROC-AUC**, và **Brier Score** (để đo độ chính xác của xác suất đầu ra).
- **Kỹ thuật lấy mẫu (Resampling):**
  - Chỉ áp dụng các kỹ thuật Oversampling (như `SMOTE`, `ADASYN`) trên **Tập Train**. 
  - Tuyệt đối không áp dụng lên tập Validation hoặc Test, vì điều này sẽ làm sai lệch phân phối thực tế của dữ liệu kiểm thử và dẫn đến kết quả đánh giá bị ảo (over-optimistic).
  - Ưu tiên sử dụng tham số tối ưu trọng số nhãn của thuật toán (`scale_pos_weight` trong LightGBM/XGBoost hoặc `class_weights` trong CatBoost/Neural Networks).

## 3. Tính Minh Bạch & Minh Giải Mô Hình (Explainable AI - XAI)

Các mô hình quyết định tài chính bắt buộc phải giải thích được để tuân thủ pháp luật và quản trị rủi ro.

- **Tích hợp SHAP/LIME:**
  - Đối với các mô hình chấm điểm tín dụng hoặc phát hiện rủi ro, bắt buộc phải cung cấp giải thích mức độ cá nhân (Local Explanation) cho từng dự đoán.
  - Đóng gói (serialize) cả `Model` và `SHAP Explainer` đi kèm nhau khi lưu trữ artifact.
- **Độ trễ suy luận (Inference Latency):**
  - Tính toán SHAP đầy đủ rất tốn tài nguyên. Trong môi trường real-time với độ trễ thấp (latency < 200ms), sử dụng `TreeSHAP` (tối ưu cho các mô hình dạng cây như LightGBM/XGBoost) hoặc chỉ tính toán SHAP cho các đặc trưng quan trọng nhất (Top K Features).

## 4. Giám Sát Mô Hình & Drift Monitoring (MLOps)

Môi trường kinh tế luôn biến động, mô hình cần được giám sát liên tục để phát hiện sự xuống cấp (Model Decay).

- **Lưu log suy luận (Inference Logging):**
  - Mọi lượt gọi API dự đoán phải được ghi log lại gồm: các thuộc tính đầu vào (features), xác suất dự đoán (probability), nhãn dự đoán (prediction) và timestamp.
- **Giám sát độ lệch (Drift Detection):**
  - Định kỳ (hàng ngày hoặc hàng tuần) sử dụng `Evidently AI` để so sánh dữ liệu thực tế thu được từ log với dữ liệu huấn luyện (Reference).
  - Tính toán chỉ số ổn định dân số **PSI (Population Stability Index)** cho các biến đầu vào quan trọng. Nếu $PSI > 0.25$, hệ thống phải phát cảnh báo yêu cầu thu thập dữ liệu mới để retrain mô hình.
