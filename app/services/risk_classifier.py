import numpy as np

class RiskClassificationEngine:
    @staticmethod
    def classify(default_probability: float) -> dict:
        """
        Maps default probability (0.0 - 1.0) into Credit Score, Risk Grade and Recommended Action.
        """
        # Ensure within range
        prob = max(0.0, min(1.0, float(default_probability)))

        # Convert to credit score (300 - 850)
        # Score goes down as default probability goes up
        credit_score = int(850 - np.floor(prob * 550))

        # Risk Classification Logic
        if prob <= 0.10:
            risk_grade = "Excellent"
            color = "#10b981"  # Emerald Green
            action = "AUTO_APPROVE"
            desc = "Hồ sơ tín dụng cực kỳ tốt. Hệ thống đề xuất DUYỆT TỰ ĐỘNG khoản vay."
        elif prob <= 0.25:
            risk_grade = "Good"
            color = "#3b82f6"  # Blue
            action = "APPROVE_WITH_CONDITIONS"
            desc = "Khách hàng có lịch sử tín dụng khá. Đề xuất duyệt vay kèm các điều khoản/giám sát bổ sung."
        elif prob <= 0.50:
            risk_grade = "Fair"
            color = "#f59e0b"  # Amber/Yellow
            action = "MANUAL_REVIEW"
            desc = "Hồ sơ tín dụng ở mức trung bình. Đề xuất chuyển sang bộ phận thẩm định thủ công để xem xét kỹ."
        else:
            risk_grade = "Poor"
            color = "#ef4444"  # Red
            action = "REJECT"
            desc = "Tỷ lệ rủi ro vỡ nợ quá cao. Hệ thống đề xuất TỪ CHỐI DUYỆT khoản vay."

        return {
            "default_probability": prob,
            "credit_score": credit_score,
            "risk_grade": risk_grade,
            "risk_color": color,
            "recommended_action": action,
            "action_description": desc
        }
