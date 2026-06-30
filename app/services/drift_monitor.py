import os
import pandas as pd
import numpy as np
from datetime import datetime
from app.config import settings
from app.database.repository import LogRepository
from sqlalchemy.ext.asyncio import AsyncSession

from evidently import Report
from evidently.presets import DataDriftPreset

class DriftMonitoringService:
    def __init__(self):
        self.reference_path = settings.REFERENCE_DATA_PATH
        self.report_dir = os.path.join(settings.STATIC_DIR, "assets", "drift_reports")
        os.makedirs(self.report_dir, exist_ok=True)

    def is_reference_ready(self) -> bool:
        return os.path.exists(self.reference_path)

    async def generate_drift_report(self, db: AsyncSession) -> dict:
        """
        Loads reference baseline and database inference logs, runs Evidently AI Data Drift Analysis,
        saves the interactive HTML report, and returns summary stats.
        """
        if not self.is_reference_ready():
            return {
                "report_generated_at": datetime.utcnow().isoformat() + "Z",
                "total_predictions_since_deploy": 0,
                "dataset_drift_detected": False,
                "drift_share": 0.0,
                "drifted_features": [],
                "target_drift": {
                    "predicted_default_rate_reference": 0.0,
                    "predicted_default_rate_current": 0.0,
                    "status": "NOT_ENOUGH_DATA"
                },
                "evidently_html_report_url": "",
                "recommendation": "Lỗi: Không tìm thấy tệp reference_data.parquet. Cần chạy ml/train.py để xuất tệp chuẩn."
            }

        # 1. Load inference logs from SQLite
        inference_logs = await LogRepository.get_all_logs_for_drift(db)
        total_logs = len(inference_logs)

        # Safety Check: Evidently requires at least some logs to run comparison
        if total_logs < 10:
            return {
                "report_generated_at": datetime.utcnow().isoformat() + "Z",
                "total_predictions_since_deploy": total_logs,
                "dataset_drift_detected": False,
                "drift_share": 0.0,
                "drifted_features": [],
                "target_drift": {
                    "predicted_default_rate_reference": 0.0,
                    "predicted_default_rate_current": 0.0,
                    "status": "NOT_ENOUGH_DATA"
                },
                "evidently_html_report_url": "",
                "recommendation": f"Chưa đủ dữ liệu thực tế để so sánh. Cần thực hiện tối thiểu 10 lượt chấm điểm tín dụng (hiện có: {total_logs})."
            }

        # 2. Convert reference and current logs to DataFrames
        ref_df = pd.read_parquet(self.reference_path)
        curr_df = pd.DataFrame(inference_logs)

        # Drop columns not used in comparison if any, ensuring both match columns
        # Keep features and target prediction column (default_probability -> TARGET)
        common_cols = list(set(ref_df.columns).intersection(set(curr_df.columns)))
        ref_df_clean = ref_df[common_cols].copy()
        curr_df_clean = curr_df[common_cols].copy()

        # Handle NaNs in current categorical data (represented as integers after label encoding)
        # evidently needs data types to match
        for col in ref_df_clean.columns:
            if ref_df_clean[col].dtype == 'object' or ref_df_clean[col].dtype.name == 'category':
                ref_df_clean[col] = ref_df_clean[col].astype(str)
                curr_df_clean[col] = curr_df_clean[col].astype(str)
            else:
                ref_df_clean[col] = pd.to_numeric(ref_df_clean[col], errors='coerce').fillna(0)
                curr_df_clean[col] = pd.to_numeric(curr_df_clean[col], errors='coerce').fillna(0)

        # 3. Configure and run Evidently Report
        report = Report(metrics=[
            DataDriftPreset()
        ])

        try:
            snapshot = report.run(reference_data=ref_df_clean, current_data=curr_df_clean)
        except Exception as e:
            return {
                "report_generated_at": datetime.utcnow().isoformat() + "Z",
                "total_predictions_since_deploy": total_logs,
                "dataset_drift_detected": False,
                "drift_share": 0.0,
                "drifted_features": [],
                "target_drift": {
                    "predicted_default_rate_reference": 0.0,
                    "predicted_default_rate_current": 0.0,
                    "status": "ERROR"
                },
                "evidently_html_report_url": "",
                "recommendation": f"Lỗi tính toán Drift từ Evidently AI: {str(e)}"
            }

        # 4. Save HTML Report
        report_filename = "latest_drift_report.html"
        report_html_path = os.path.join(self.report_dir, report_filename)
        snapshot.save_html(report_html_path)

        # 5. Extract JSON results for summary stats
        report_json = snapshot.dict()
        
        # Parse metric values from JSON output structure of Evidently AI 0.7.21
        metrics_results = report_json.get('metrics', [])
        
        drift_share = 0.0
        dataset_drift_detected = False
        drifted_features_summary = []
        target_drift_detected = False

        for metric in metrics_results:
            config = metric.get('config', {})
            metric_type = config.get('type', '')
            val = metric.get('value')
            
            if 'DriftedColumnsCount' in metric_type:
                if isinstance(val, dict):
                    drift_share = val.get('share', 0.0)
                    drift_threshold = config.get('drift_share', 0.5)
                    dataset_drift_detected = drift_share >= drift_threshold
                
            elif 'ValueDrift' in metric_type:
                col = config.get('column')
                threshold = config.get('threshold', 0.05)
                p_value = float(val) if val is not None else 1.0
                is_drifted = p_value < threshold
                
                # Check if this is the target column
                if col == 'TARGET':
                    target_drift_detected = is_drifted
                
                # Map this into our format
                drifted_features_summary.append({
                    "feature": col if col is not None else "Unknown",
                    "psi": p_value,  # Pass p-value as the score
                    "status": "DRIFTED" if is_drifted else "STABLE",
                    "alert": "WARNING" if is_drifted else "OK"
                })

        # Fallback means from original dataframes
        ref_target_mean = float(ref_df_clean['TARGET'].mean()) if 'TARGET' in ref_df_clean.columns else 0.0
        curr_target_mean = float(curr_df_clean['TARGET'].mean()) if 'TARGET' in curr_df_clean.columns else 0.0

        # Recommendation logic
        if dataset_drift_detected:
            rec = "Cảnh báo: Phát hiện sự lệch dữ liệu trên hệ thống (Dataset Drift). Đề nghị thu thập thêm mẫu và chuẩn bị huấn luyện lại mô hình."
        elif len([f for f in drifted_features_summary if f["alert"] == "WARNING"]) > 0:
            rec = "Một số thuộc tính đầu vào quan trọng có sự lệch nhẹ. Cần tiếp tục theo dõi các chỉ số."
        else:
            rec = "Hệ thống hoạt động ổn định. Phân phối dữ liệu thực tế khớp tốt với dữ liệu huấn luyện."

        return {
            "report_generated_at": datetime.utcnow().isoformat() + "Z",
            "total_predictions_since_deploy": total_logs,
            "dataset_drift_detected": dataset_drift_detected,
            "drift_share": float(drift_share),
            "drifted_features": drifted_features_summary,
            "target_drift": {
                "predicted_default_rate_reference": ref_target_mean,
                "predicted_default_rate_current": curr_target_mean,
                "status": "DRIFTED" if target_drift_detected else "STABLE"
            },
            "evidently_html_report_url": f"/static/assets/drift_reports/{report_filename}",
            "recommendation": rec
        }
