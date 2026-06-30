"""
CreditLens AI — Exploratory Data Analysis (EDA) & Visualization Script
Designed for Kaggle Notebooks.

Copy-paste toàn bộ file này vào 1 cell trên Kaggle Notebook để xuất ra các biểu đồ 
phân tích quan trọng (key insights) của bộ dữ liệu Home Credit Default Risk.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set style for high-quality plots
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = [10, 6]
plt.rcParams['font.size'] = 11

def main():
    # 1. Load Data
    raw_dir = '../input/home-credit-default-risk' if os.path.exists('/kaggle') else 'home-credit-default-risk'
    app_path = os.path.join(raw_dir, 'application_train.csv')
    
    print("--- Loading data for EDA ---")
    if not os.path.exists(app_path):
        print(f"Error: Missing {app_path}. Add dataset to Kaggle.")
        return
        
    df = pd.read_csv(app_path)
    print(f"Dataset shape: {df.shape}")
    
    # Preprocess a few columns for plotting
    df['age'] = -df['DAYS_BIRTH'] / 365.25
    df['employment_years'] = -df['DAYS_EMPLOYED'].replace(365243, np.nan) / 365.25
    df['payment_rate'] = df['AMT_ANNUITY'] / (df['AMT_CREDIT'] + 1)
    df['income_per_person'] = df['AMT_INCOME_TOTAL'] / (df['CNT_CHILDREN'] + 2)
    
    os.makedirs('eda_plots', exist_ok=True)
    
    # -------------------------------------------------------------
    # PLOT 1: Class Imbalance (Phân phối nhãn mục tiêu)
    # -------------------------------------------------------------
    print("Plotting Class Distribution...")
    plt.figure(figsize=(7, 5))
    target_counts = df['TARGET'].value_counts(normalize=True) * 100
    ax = sns.barplot(x=target_counts.index, y=target_counts.values, palette=['#10b981', '#ef4444'])
    plt.title('Tỷ lệ phân phối nhãn TARGET (Default vs Repaid)', fontsize=13, weight='bold', pad=15)
    plt.xlabel('Trạng thái (0 = Trả nợ đúng hạn, 1 = Nợ quá hạn/Vỡ nợ)', labelpad=10)
    plt.ylabel('Tỷ lệ phần trăm (%)')
    plt.xticks([0, 1], ['Repaid (91.8%)', 'Default (8.2%)'])
    
    # Add values on top of bars
    for p in ax.patches:
        ax.annotate(f"{p.get_height():.1f}%", (p.get_x() + p.get_width() / 2., p.get_height() + 0.5),
                    ha='center', va='center', xytext=(0, 5), textcoords='offset points', weight='bold')
    plt.tight_layout()
    plt.savefig('eda_plots/1_class_imbalance.png', dpi=150)
    plt.close()

    # -------------------------------------------------------------
    # PLOT 2: Age Distribution vs Default Rate (Độ tuổi vs Tỷ lệ nợ xấu)
    # -------------------------------------------------------------
    print("Plotting Age vs Default Rate...")
    # Bin ages into groups
    df['age_group'] = pd.cut(df['age'], bins=[20, 30, 40, 50, 60, 70], labels=['20-30', '30-40', '40-50', '50-60', '60-70'])
    age_group_defaults = df.groupby('age_group')['TARGET'].mean() * 100
    
    plt.figure(figsize=(8, 5))
    ax = sns.barplot(x=age_group_defaults.index, y=age_group_defaults.values, palette='Blues_r')
    plt.title('Tỷ lệ nợ xấu theo nhóm tuổi', fontsize=13, weight='bold', pad=15)
    plt.xlabel('Độ tuổi khách hàng (Năm)', labelpad=10)
    plt.ylabel('Tỷ lệ nợ xấu (%)')
    
    for p in ax.patches:
        ax.annotate(f"{p.get_height():.2f}%", (p.get_x() + p.get_width() / 2., p.get_height() + 0.1),
                    ha='center', va='center', xytext=(0, 5), textcoords='offset points', weight='bold')
    plt.tight_layout()
    plt.savefig('eda_plots/2_age_vs_default.png', dpi=150)
    plt.close()

    # -------------------------------------------------------------
    # PLOT 3: External Source 3 vs Default Rate (Mối quan hệ tuyến tính mạnh nhất)
    # -------------------------------------------------------------
    print("Plotting External Source 3 impact...")
    plt.figure(figsize=(9, 5))
    sns.kdeplot(df[df['TARGET'] == 0]['EXT_SOURCE_3'], label='Trả nợ tốt (Target=0)', fill=True, color='#10b981', alpha=0.3)
    sns.kdeplot(df[df['TARGET'] == 1]['EXT_SOURCE_3'], label='Vỡ nợ (Target=1)', fill=True, color='#ef4444', alpha=0.3)
    plt.title('Phân phối điểm tín dụng EXT_SOURCE_3 theo nhóm khách hàng', fontsize=13, weight='bold', pad=15)
    plt.xlabel('Điểm số EXT_SOURCE_3 (Châm bởi bên thứ ba)')
    plt.ylabel('Mật độ phân phối (KDE)')
    plt.legend(loc='upper right')
    plt.tight_layout()
    plt.savefig('eda_plots/3_ext_source_3_kde.png', dpi=150)
    plt.close()

    # -------------------------------------------------------------
    # PLOT 4: payment_rate vs Default Rate (Sự hiệu quả của Engineered Feature)
    # -------------------------------------------------------------
    print("Plotting Payment Rate impact...")
    # Bin payment rate into quantiles
    df['payment_rate_bin'] = pd.qcut(df['payment_rate'], q=5, labels=['Rất Thấp', 'Thấp', 'Trung Bình', 'Cao', 'Rất Cao'])
    pay_rate_defaults = df.groupby('payment_rate_bin')['TARGET'].mean() * 100
    
    plt.figure(figsize=(8, 5))
    ax = sns.barplot(x=pay_rate_defaults.index, y=pay_rate_defaults.values, palette='Oranges')
    plt.title('Tỷ lệ nợ xấu theo Tỷ lệ trả nợ góp (Payment Rate)', fontsize=13, weight='bold', pad=15)
    plt.xlabel('Phân nhóm Tỷ lệ trả nợ (Payment Rate = Annuity / Credit)', labelpad=10)
    plt.ylabel('Tỷ lệ nợ xấu (%)')
    
    for p in ax.patches:
        ax.annotate(f"{p.get_height():.2f}%", (p.get_x() + p.get_width() / 2., p.get_height() + 0.1),
                    ha='center', va='center', xytext=(0, 5), textcoords='offset points', weight='bold')
    plt.tight_layout()
    plt.savefig('eda_plots/4_payment_rate_vs_default.png', dpi=150)
    plt.close()

    print("\n--- EDA Completed! ---")
    print("All plots saved in 'eda_plots/' directory. You can download and inspect them.")

if __name__ == '__main__':
    main()
