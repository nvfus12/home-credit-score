// Monitoring Tab Logic
const Monitoring = {
    statsTotal: null,
    statsToday: null,
    statsAvg: null,
    healthBanner: null,
    healthTitle: null,
    healthDesc: null,
    driftWarningBox: null,
    driftWarningText: null,
    driftReportContainer: null,
    driftReportIframe: null,

    init() {
        this.statsTotal = document.getElementById('stats-total-inferences');
        this.statsToday = document.getElementById('stats-today-inferences');
        this.statsAvg = document.getElementById('stats-avg-probability');
        
        this.healthBanner = document.getElementById('system-health-banner');
        this.healthTitle = document.getElementById('system-health-title');
        this.healthDesc = document.getElementById('system-health-desc');
        
        this.driftWarningBox = document.getElementById('drift-warning-box');
        this.driftWarningText = document.getElementById('drift-warning-text');
        this.driftReportContainer = document.getElementById('drift-report-container');
        this.driftReportIframe = document.getElementById('drift-report-iframe');
    },

    async loadMonitoringData() {
        await this.loadStats();
        await this.loadDriftReport();
    },

    async loadStats() {
        try {
            const data = await API.get('/monitoring/stats');
            
            // Update stats cards
            if (this.statsTotal) this.statsTotal.innerText = data.total_predictions;
            if (this.statsToday) this.statsToday.innerText = data.today_predictions;
            if (this.statsAvg) this.statsAvg.innerText = `${(data.avg_default_probability * 100).toFixed(1)}%`;

            // Update System Health Banner style
            if (this.healthBanner) {
                this.healthBanner.className = 'alert-banner';
                if (data.system_health === 'OK') {
                    this.healthBanner.classList.add('alert-banner-ok');
                    this.healthTitle.innerHTML = '<i class="fa-solid fa-circle-check fa-lg"></i> Hệ thống đang hoạt động ổn định (Health: OK)';
                    this.healthDesc.innerText = 'Mô hình XGBoost đang hoạt động hiệu quả. Không phát hiện sai lệch phân phối (Data Drift).';
                } else {
                    this.healthBanner.classList.add('alert-banner-warning');
                    this.healthTitle.innerHTML = '<i class="fa-solid fa-triangle-exclamation fa-lg"></i> Phát hiện cảnh báo hệ thống (Health: WARNING)';
                    this.healthDesc.innerText = `Cảnh báo active: ${data.active_alerts.join(', ')}. Hãy kiểm tra báo cáo Data Drift bên dưới.`;
                }
            }
        } catch (error) {
            console.error("Failed to load monitoring stats", error);
        }
    },

    async loadDriftReport() {
        try {
            // Update loading text
            this.driftWarningText.innerText = "Đang tính toán phân tích độ lệch dữ liệu (Evidently AI)...";
            this.driftWarningBox.style.display = 'block';
            this.driftReportContainer.style.display = 'none';

            const data = await API.get('/monitoring/drift-report');

            // Check if there was enough data to generate report
            if (data.target_drift.status === 'NOT_ENOUGH_DATA') {
                this.driftWarningBox.style.display = 'block';
                this.driftWarningText.innerHTML = `
                    <i class="fa-solid fa-triangle-exclamation fa-3x" style="color: var(--accent-yellow); margin-bottom: 1rem;"></i>
                    <p><strong>Chưa đủ dữ liệu thực tế để chạy báo cáo Data Drift.</strong></p>
                    <p style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.5rem;">${data.recommendation}</p>
                `;
                this.driftReportContainer.style.display = 'none';
            } else if (data.evidently_html_report_url) {
                // Show iframe and load report
                this.driftWarningBox.style.display = 'none';
                this.driftReportContainer.style.display = 'block';
                
                // Add timestamp to bypass iframe cache
                this.driftReportIframe.src = `${data.evidently_html_report_url}?t=${new Date().getTime()}`;
            } else {
                throw new Error("Invalid report response");
            }
        } catch (error) {
            this.driftWarningBox.style.display = 'block';
            this.driftWarningText.innerHTML = `
                <i class="fa-solid fa-circle-exclamation fa-3x" style="color: var(--accent-red); margin-bottom: 1rem;"></i>
                <p><strong>Lỗi tải báo cáo MLOps:</strong></p>
                <p style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.5rem;">${error.message}</p>
            `;
            this.driftReportContainer.style.display = 'none';
        }
    }
};
