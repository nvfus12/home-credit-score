// Main Application Controller & History Tab Logic

const HistoryTab = {
    currentPage: 1,
    limit: 10,
    totalRecords: 0,
    
    // UI elements
    tableBody: null,
    pageInfo: null,
    btnPrev: null,
    btnNext: null,
    filterRisk: null,

    init() {
        this.tableBody = document.getElementById('history-table-body');
        this.pageInfo = document.getElementById('history-page-info');
        this.btnPrev = document.getElementById('btn-history-prev');
        this.btnNext = document.getElementById('btn-history-next');
        this.filterRisk = document.getElementById('history-filter-risk');

        // Bind events
        if (this.btnPrev) this.btnPrev.addEventListener('click', () => this.changePage(-1));
        if (this.btnNext) this.btnNext.addEventListener('click', () => this.changePage(1));
        if (this.filterRisk) {
            this.filterRisk.addEventListener('change', () => {
                this.currentPage = 1;
                this.loadHistory();
            });
        }
    },

    async loadHistory() {
        if (!this.tableBody) return;

        this.tableBody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--text-secondary); padding: 3rem 0;"><i class="spinner"></i> Đang tải dữ liệu lịch sử...</td></tr>';

        const riskGrade = this.filterRisk ? this.filterRisk.value : '';
        const endpoint = `/predictions/history?page=${this.currentPage}&limit=${this.limit}${riskGrade ? `&risk_grade=${riskGrade}` : ''}`;

        try {
            const data = await API.get(endpoint);
            this.totalRecords = data.total_records;
            this.renderHistory(data.items);
            this.updatePaginationControls();
        } catch (error) {
            this.tableBody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--accent-red); padding: 3rem 0;"><i class="fa-solid fa-circle-xmark"></i> Lỗi: ${error.message}</td></tr>`;
        }
    },

    renderHistory(items) {
        if (items.length === 0) {
            this.tableBody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--text-secondary); padding: 3rem 0;"><i class="fa-solid fa-folder-open fa-2x" style="margin-bottom: 0.5rem; color: var(--text-muted);"></i><p>Không tìm thấy hồ sơ nào khớp với điều kiện.</p></td></tr>';
            return;
        }

        this.tableBody.innerHTML = '';
        items.forEach(item => {
            const tr = document.createElement('tr');
            
            // Format Timestamp
            const date = new Date(item.timestamp);
            const formattedDate = date.toLocaleString('vi-VN', { 
                day: '2-digit', 
                month: '2-digit', 
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });

            // Action Name Formatting
            const actionText = Underwriting.formatActionName(item.recommended_action);
            const probPercent = (item.default_probability * 100).toFixed(1) + '%';
            
            // Set row content
            tr.innerHTML = `
                <td>${formattedDate}</td>
                <td><code style="color: var(--accent-blue); font-weight: bold;">${item.prediction_id}</code></td>
                <td>${item.applicant_name}</td>
                <td>${(item.income_total).toLocaleString('vi-VN')} đ</td>
                <td>${(item.loan_amount).toLocaleString('vi-VN')} đ</td>
                <td>${probPercent}</td>
                <td><strong style="color: var(--text-primary);">${item.credit_score}</strong></td>
                <td><span class="badge badge-${item.risk_grade.toLowerCase()}">${item.risk_grade}</span></td>
            `;

            // Hover row to allow inspect? (Can be added as premium feature)
            this.tableBody.appendChild(tr);
        });
    },

    changePage(direction) {
        this.currentPage += direction;
        this.loadHistory();
    },

    updatePaginationControls() {
        const totalPages = Math.ceil(this.totalRecords / this.limit) || 1;
        this.pageInfo.innerText = `Trang ${this.currentPage} / ${totalPages} (Tổng số ${this.totalRecords} bản ghi)`;

        this.btnPrev.disabled = this.currentPage === 1;
        this.btnNext.disabled = this.currentPage >= totalPages;
    }
};

// Global App setup
document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Tabs navigation
    const navItems = document.querySelectorAll('.nav-item');
    const tabContents = document.querySelectorAll('.tab-content');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const tabName = item.getAttribute('data-tab');
            
            // Remove active classes
            navItems.forEach(nav => nav.classList.remove('active'));
            tabContents.forEach(tab => tab.classList.remove('active'));
            
            // Set active
            item.classList.add('active');
            const targetTab = document.getElementById(`tab-${tabName}`);
            if (targetTab) targetTab.classList.add('active');

            // Trigger specific loaders
            if (tabName === 'history') {
                HistoryTab.loadHistory();
            } else if (tabName === 'monitoring') {
                Monitoring.loadMonitoringData();
            }
        });
    });

    // 2. Initialize Module Controller Objects
    Underwriting.init();
    HistoryTab.init();
    Monitoring.init();

    console.log("CreditLens AI Frontend Initialized.");
});
