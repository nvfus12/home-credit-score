# Từ Điển Đặc Trưng (Feature Dictionary & Financial Logic)

Tài liệu này giải thích ý nghĩa nghiệp vụ tài chính của các đặc trưng (features) đầu vào và các đặc trưng tự tạo (engineered features) dùng trong mô hình **CreditLens AI**.

---

## 1. Các Đặc Trưng Được Tạo Tự Động (Engineered Financial Features)

Mô hình học máy dự báo rủi ro tín dụng phụ thuộc rất nhiều vào các chỉ số tương đối (Ratios) phản ánh áp lực nợ vay lên thu nhập khách hàng. Dự án tạo ra các tỷ lệ tài chính sau:

| Đặc trưng | Ý nghĩa nghiệp vụ | Cách tính | Diễn giải tài chính |
| :--- | :--- | :--- | :--- |
| `loan_to_income_ratio` | Tỷ lệ tổng nợ vay trên thu nhập | $\frac{\text{loan\_amount}}{\text{income\_total} + 1}$ | Đo lường xem khoản vay lớn gấp bao nhiêu lần thu nhập hàng tháng. Tỷ lệ này càng lớn thì rủi ro mất khả năng thanh toán càng cao. |
| `annuity_to_income_ratio` | Tỷ lệ trả góp định kỳ trên thu nhập | $\frac{\text{loan\_annuity}}{\text{income\_total} + 1}$ | Thể hiện gánh nặng trả nợ hàng tháng của khách hàng. Theo quy chuẩn quản lý rủi ro ngân hàng, tỷ lệ này không nên vượt quá **35% - 40%** để tránh vỡ nợ. |
| `credit_to_goods_ratio` | Tỷ lệ khoản vay trên trị giá tài sản mua | $\frac{\text{loan\_amount}}{\text{goods\_price} + 1}$ | Phản ánh tỷ lệ tài trợ vốn của khoản vay. Nếu khách hàng vay nhiều hơn trị giá hàng hóa thực tế mua (Tỷ lệ > 1), rủi ro đạo đức (moral hazard) tăng lên. |

---

## 2. Các Đặc Trưng Tổng Hợp Lịch Sử Tín Dụng (Aggregated Historical Features)

Hệ thống kết nối và tổng hợp thông tin lịch sử của khách hàng từ 2 nguồn: Lịch sử tín dụng bên ngoài (CIC) và Lịch sử tín dụng nội bộ trong quá khứ.

| Đặc trưng | Nguồn dữ liệu | Cách tính | Diễn giải tài chính |
| :--- | :--- | :--- | :--- |
| `bureau_loans_active` | Lịch sử CIC (`bureau.csv`) | Đếm số lượng bản ghi có trạng thái `CREDIT_ACTIVE == 'Active'` | Khách hàng đang có quá nhiều khoản vay hoạt động đồng thời tại các tổ chức tín dụng khác sẽ có nguy cơ rơi vào bẫy nợ nần chồng chất. |
| `bureau_overdue_count` | Lịch sử CIC (`bureau.csv`) | Đếm số lượng khoản vay có `CREDIT_DAY_OVERDUE > 0` | Số lần nợ quá hạn tại các ngân hàng khác là biến số có trọng số giải thích cao nhất về lịch sử nợ xấu tín dụng CIC. |
| `prev_application_count` | Lịch sử nội bộ (`prev_app.csv`) | Đếm tổng số hồ sơ vay cũ của khách hàng tại Home Credit | Thể hiện mức độ gắn kết lâu dài của khách hàng với tổ chức. |
| `prev_approved_ratio` | Lịch sử nội bộ (`prev_app.csv`) | $\frac{\text{approved\_applications}}{\text{total\_applications}}$ | Tỷ lệ hồ sơ được duyệt trong quá khứ. Nếu khách hàng liên tục bị từ chối vay trước đây, tỷ lệ duyệt thấp ngầm hiểu rủi ro cao. |

---

## 3. Các Đặc Trưng Hồ Sơ Khách Hàng (Customer Profile Features)

| Đặc trưng | Kiểu dữ liệu | Diễn giải tài chính |
| :--- | :--- | :--- |
| `applicant_age` | Numeric (float) | Tuổi của khách hàng tại thời điểm làm đơn vay (quy đổi từ số ngày âm `DAYS_BIRTH`). Nhóm tuổi quá trẻ thường có rủi ro vỡ nợ cao hơn do thu nhập chưa ổn định. |
| `employment_years` | Numeric (float) | Số năm làm việc liên tục tại công việc hiện tại. Thể hiện sự ổn định nghề nghiệp và dòng tiền thu nhập. |
| `NAME_EDUCATION_TYPE` | Categorical (Encoded) | Trình độ học vấn cao (Đại học/Sau đại học) thường tương quan tỷ lệ nghịch với rủi ro vỡ nợ. |
| `NAME_HOUSING_TYPE` | Categorical (Encoded) | Hình thức cư trú (sở hữu nhà riêng, ở chung bố mẹ hay thuê nhà) phản ánh mức độ tự chủ tài chính. |
| `EXT_SOURCE_1, 2, 3` | Numeric (float) | Điểm số tín nhiệm từ các nguồn chấm điểm bên thứ ba độc lập (Credit Bureau Scores). Đây là các thuộc tính dự báo mạnh nhất của mô hình. |
