import os
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt
import shap
import pandas as pd
import numpy as np
from app.config import settings

class SHAPExplanationService:
    def __init__(self, scorer_service):
        self.scorer = scorer_service
        self.explainer = None
        self.feature_names_mapping = {
            'applicant_age': 'Tuổi khách hàng',
            'income_total': 'Thu nhập hàng tháng',
            'employment_years': 'Số năm làm việc',
            'loan_amount': 'Số tiền xin vay',
            'loan_annuity': 'Số tiền trả góp định kỳ',
            'goods_price': 'Giá trị tài sản mua',
            'num_children': 'Số con cái',
            'NAME_EDUCATION_TYPE': 'Trình độ học vấn',
            'NAME_HOUSING_TYPE': 'Hình thức cư trú',
            'bureau_loans_active': 'Số khoản vay CIC đang hoạt động',
            'bureau_overdue_count': 'Số khoản nợ CIC quá hạn',
            'prev_application_count': 'Số hồ sơ vay cũ tại Home Credit',
            'prev_approved_ratio': 'Tỷ lệ duyệt hồ sơ cũ',
            'EXT_SOURCE_1': 'Điểm tín dụng đối tác 1',
            'EXT_SOURCE_2': 'Điểm tín dụng đối tác 2',
            'EXT_SOURCE_3': 'Điểm tín dụng đối tác 3',
            'loan_to_income_ratio': 'Tỷ lệ nợ/thu nhập',
            'annuity_to_income_ratio': 'Tỷ lệ trả góp/thu nhập',
            'credit_to_goods_ratio': 'Tỷ lệ vay/trị giá hàng hóa',
            'external_source_mean': 'Điểm tín dụng TB đối tác',
            'external_source_std': 'Độ lệch điểm tín dụng'
        }
        self.init_explainer()

    def init_explainer(self):
        """Initializes the SHAP TreeExplainer if model is ready."""
        if self.scorer.is_ready():
            try:
                print("Initializing TreeSHAP Explainer...")
                # TreeExplainer is highly optimized for tree models
                self.explainer = shap.TreeExplainer(self.scorer.model)
                print("TreeSHAP Explainer initialized.")
            except Exception as e:
                print(f"Error initializing TreeSHAP: {e}")
                self.explainer = None

    def explain_and_plot(self, prediction_id: str, input_dict: dict) -> dict:
        """
        Generates SHAP values for a single prediction, saves a transparent dark-themed
        SHAP plot to static assets, and returns the top driving features.
        """
        if not self.scorer.is_ready():
            raise RuntimeError("Scoring service artifacts are not loaded.")
        if self.explainer is None:
            self.init_explainer()
            if self.explainer is None:
                raise RuntimeError("SHAP explainer failed to initialize.")

        # 1. Transform single input to matching dataframe row
        df_row = self.scorer.get_features_df(input_dict)

        # 2. Compute SHAP values
        # shap_values is a list for multi-class, or array for binary (we use [1] or check shape)
        shap_values_obj = self.explainer(df_row)
        
        # For binary classification, shap_values_obj has .values [samples, features]
        # In newer SHAP versions, explainer returns Explanation object
        shap_val = shap_values_obj.values[0]
        base_val = shap_values_obj.base_values[0]
        
        # Create dictionary of raw feature names -> shap values
        feature_shaps = dict(zip(df_row.columns, shap_val))

        # 3. Build top risk factors description list
        factors = []
        for feat, val in feature_shaps.items():
            display_name = self.feature_names_mapping.get(feat, feat)
            direction = "risk_increase" if val > 0 else "risk_decrease"
            
            # Simple business rules for descriptions
            if val > 0:
                desc = f"Chỉ số {display_name} làm tăng nguy cơ nợ xấu (mức độ ảnh hưởng: +{abs(val):.3f})."
            else:
                desc = f"Chỉ số {display_name} giúp giảm thiểu nguy cơ nợ xấu (mức độ ảnh hưởng: -{abs(val):.3f})."

            factors.append({
                "feature": feat,
                "display_name": display_name,
                "shap_value": float(val),
                "direction": direction,
                "description": desc
            })

        # Sort factors by absolute SHAP value (highest impact first)
        factors = sorted(factors, key=lambda x: abs(x["shap_value"]), reverse=True)
        top_factors = factors[:6]  # Return top 6 contributors

        # 4. Generate Dark Theme SHAP Plot
        plot_filename = f"{prediction_id}.png"
        plot_path = os.path.join(settings.SHAP_PLOT_DIR, plot_filename)
        self._generate_dark_plot(shap_values_obj[0], plot_path)

        return {
            "shap_plot_url": f"/static/assets/shap_plots/{plot_filename}",
            "top_risk_factors": top_factors,
            "total_features_analyzed": len(df_row.columns)
        }

    def _generate_dark_plot(self, shap_explanation_single, output_path):
        """Creates a custom, highly styled dark theme horizontal bar plot for SHAP."""
        # Get data
        shap_vals = shap_explanation_single.values
        features = shap_explanation_single.data
        feature_names = shap_explanation_single.feature_names

        # Map to display names
        display_names = [self.feature_names_mapping.get(name, name) for name in feature_names]

        # Combine and sort by absolute SHAP value
        data = list(zip(display_names, shap_vals, features))
        # Sort by absolute impact
        data_sorted = sorted(data, key=lambda x: abs(x[1]))
        
        # Take top 10 features for visualization
        top_data = data_sorted[-10:] if len(data_sorted) > 10 else data_sorted

        names = [x[0] for x in top_data]
        vals = [x[1] for x in top_data]
        
        # Set up plot style for dark mode
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(8, 5))
        
        # Custom transparent background
        fig.patch.set_facecolor('none')
        ax.set_facecolor('none')

        # Color mapping: red for positive SHAP (increases default probability), blue/green for negative
        # Hex codes match Glassmorphism dark palette
        colors = ['#ef4444' if v > 0 else '#10b981' for v in vals]
        
        bars = ax.barh(names, vals, color=colors, edgecolor='none', height=0.6)

        # Labels & Styling
        ax.set_title("Đóng Góp Của Các Yếu Tố Rủi Ro (TreeSHAP Analysis)", color='#F1F5F9', fontsize=12, pad=15)
        ax.set_xlabel("Tác động tới tỷ lệ nợ xấu (Log-Odds Impact)", color='#94A3B8', fontsize=10, labelpad=10)
        
        ax.tick_params(colors='#94A3B8', labelsize=9)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#1e293b')
        ax.spines['bottom'].set_color('#1e293b')
        
        # Add values next to the bars
        for bar in bars:
            width = bar.get_width()
            align = 'left' if width < 0 else 'right'
            offset = -3 if width < 0 else 3
            ax.annotate(
                f"{width:+.3f}",
                xy=(width, bar.get_y() + bar.get_height() / 2),
                xytext=(offset, 0),
                textcoords="offset points",
                ha=align, va='center',
                color='#F1F5F9', fontsize=8,
                weight='bold'
            )

        # Add vertical line at zero
        ax.axvline(0, color='#334155', linestyle='--', linewidth=1)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='none', transparent=True)
        plt.close()
