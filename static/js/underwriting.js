// Underwriting Tab Logic
const Underwriting = {
    form: null,
    btnAssess: null,
    resultsEmpty: null,
    resultsLoading: null,
    resultsContent: null,
    
    // Circle SVG config
    maxCircumference: 534, // 2 * PI * r (85)

    // 10 Diverse Predefined Profiles for Testing
    templates: {
        profile1: {
            applicant_age: 45,
            num_children: 0,
            education_type: "Higher education",
            housing_type: "House / apartment",
            income_total: 60000000,
            employment_years: 15,
            loan_amount: 100000000,
            loan_annuity: 3500000,
            goods_price: 120000000,
            bureau_loans_active: 0,
            bureau_overdue_count: 0,
            prev_application_count: 2,
            prev_approved_ratio: 1.0,
            external_source_2: 0.85,
            external_source_3: 0.90
        },
        profile2: {
            applicant_age: 35,
            num_children: 1,
            education_type: "Higher education",
            housing_type: "House / apartment",
            income_total: 30000000,
            employment_years: 8,
            loan_amount: 150000000,
            loan_annuity: 7000000,
            goods_price: 150000000,
            bureau_loans_active: 1,
            bureau_overdue_count: 0,
            prev_application_count: 1,
            prev_approved_ratio: 1.0,
            external_source_2: 0.65,
            external_source_3: 0.68
        },
        profile3: {
            applicant_age: 28,
            num_children: 2,
            education_type: "Secondary / special education",
            housing_type: "Rented apartment",
            income_total: 15000000,
            employment_years: 3,
            loan_amount: 200000000,
            loan_annuity: 10000000,
            goods_price: 180000000,
            bureau_loans_active: 2,
            bureau_overdue_count: 0,
            prev_application_count: 3,
            prev_approved_ratio: 0.67,
            external_source_2: 0.45,
            external_source_3: 0.52
        },
        profile4: {
            applicant_age: 24,
            num_children: 0,
            education_type: "Secondary / special education",
            housing_type: "With parents",
            income_total: 8000000,
            employment_years: 1,
            loan_amount: 300000000,
            loan_annuity: 25000000,
            goods_price: 280000000,
            bureau_loans_active: 4,
            bureau_overdue_count: 2,
            prev_application_count: 2,
            prev_approved_ratio: 0.0,
            external_source_2: 0.15,
            external_source_3: 0.12
        },
        profile5: {
            applicant_age: 52,
            num_children: 0,
            education_type: "Higher education",
            housing_type: "House / apartment",
            income_total: 120000000,
            employment_years: 20,
            loan_amount: 250000000,
            loan_annuity: 8500000,
            goods_price: 300000000,
            bureau_loans_active: 0,
            bureau_overdue_count: 0,
            prev_application_count: 0,
            prev_approved_ratio: 0.0,
            external_source_2: 0.88,
            external_source_3: 0.85
        },
        profile6: {
            applicant_age: 27,
            num_children: 0,
            education_type: "Higher education",
            housing_type: "House / apartment",
            income_total: 40000000,
            employment_years: 4,
            loan_amount: 100000000,
            loan_annuity: 5000000,
            goods_price: 100000000,
            bureau_loans_active: 1,
            bureau_overdue_count: 0,
            prev_application_count: 1,
            prev_approved_ratio: 1.0,
            external_source_2: 0.58,
            external_source_3: 0.72
        },
        profile7: {
            applicant_age: 40,
            num_children: 3,
            education_type: "Secondary / special education",
            housing_type: "House / apartment",
            income_total: 25000000,
            employment_years: 6,
            loan_amount: 350000000,
            loan_annuity: 18000000,
            goods_price: 320000000,
            bureau_loans_active: 3,
            bureau_overdue_count: 0,
            prev_application_count: 4,
            prev_approved_ratio: 0.75,
            external_source_2: 0.38,
            external_source_3: 0.45
        },
        profile8: {
            applicant_age: 33,
            num_children: 2,
            education_type: "Secondary / special education",
            housing_type: "Rented apartment",
            income_total: 10000000,
            employment_years: 2,
            loan_amount: 80000000,
            loan_annuity: 6000000,
            goods_price: 70000000,
            bureau_loans_active: 2,
            bureau_overdue_count: 1,
            prev_application_count: 2,
            prev_approved_ratio: 0.5,
            external_source_2: 0.22,
            external_source_3: 0.19
        },
        profile9: {
            applicant_age: 48,
            num_children: 1,
            education_type: "Higher education",
            housing_type: "House / apartment",
            income_total: 180000000,
            employment_years: 12,
            loan_amount: 500000000,
            loan_annuity: 15000000,
            goods_price: 550000000,
            bureau_loans_active: 1,
            bureau_overdue_count: 0,
            prev_application_count: 3,
            prev_approved_ratio: 1.0,
            external_source_2: 0.82,
            external_source_3: 0.91
        },
        profile10: {
            applicant_age: 22,
            num_children: 0,
            education_type: "Secondary / special education",
            housing_type: "Rented apartment",
            income_total: 5000000,
            employment_years: 0,
            loan_amount: 120000000,
            loan_annuity: 10000000,
            goods_price: 100000000,
            bureau_loans_active: 5,
            bureau_overdue_count: 3,
            prev_application_count: 1,
            prev_approved_ratio: 0.0,
            external_source_2: 0.08,
            external_source_3: 0.05
        }
    },

    init() {
        this.form = document.getElementById('loan-form');
        this.btnAssess = document.getElementById('btn-assess');
        this.resultsEmpty = document.getElementById('results-empty');
        this.resultsLoading = document.getElementById('results-loading');
        this.resultsContent = document.getElementById('results-content');

        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleAssessment(e));
        }

        // Hook up Template Select and Clear buttons
        const templateSelect = document.getElementById('template-select');
        if (templateSelect) {
            templateSelect.addEventListener('change', (e) => this.loadTemplate(e.target.value));
        }

        const btnClearForm = document.getElementById('btn-clear-form');
        if (btnClearForm) {
            btnClearForm.addEventListener('click', () => this.clearForm());
        }
    },

    loadTemplate(profileKey) {
        const data = this.templates[profileKey];
        if (!data) return;

        document.getElementById('applicant_age').value = data.applicant_age;
        document.getElementById('num_children').value = data.num_children;
        document.getElementById('education_type').value = data.education_type;
        document.getElementById('housing_type').value = data.housing_type;
        document.getElementById('income_total').value = data.income_total;
        document.getElementById('employment_years').value = data.employment_years;
        document.getElementById('loan_amount').value = data.loan_amount;
        document.getElementById('loan_annuity').value = data.loan_annuity;
        document.getElementById('goods_price').value = data.goods_price;
        document.getElementById('bureau_loans_active').value = data.bureau_loans_active;
        document.getElementById('bureau_overdue_count').value = data.bureau_overdue_count;
        document.getElementById('prev_application_count').value = data.prev_application_count;
        document.getElementById('prev_approved_ratio').value = data.prev_approved_ratio;
        document.getElementById('external_source_2').value = data.external_source_2;
        document.getElementById('external_source_3').value = data.external_source_3;
    },

    clearForm() {
        if (this.form) {
            this.form.reset();
        }
        
        const templateSelect = document.getElementById('template-select');
        if (templateSelect) {
            templateSelect.value = "";
        }
        
        // Return to empty state
        this.resultsEmpty.style.display = 'block';
        this.resultsContent.style.display = 'none';
        this.resultsLoading.style.display = 'none';
    },

    async handleAssessment(e) {
        e.preventDefault();
        
        // Show loading state
        this.resultsEmpty.style.display = 'none';
        this.resultsContent.style.display = 'none';
        this.resultsLoading.style.display = 'block';
        this.btnAssess.disabled = true;
        this.btnAssess.innerHTML = '<i class="spinner"></i> <span>Đang xử lý phân tích...</span>';

        // Extract values from form
        const payload = {
            applicant_age: parseFloat(document.getElementById('applicant_age').value),
            income_total: parseFloat(document.getElementById('income_total').value),
            employment_years: parseFloat(document.getElementById('employment_years').value),
            loan_amount: parseFloat(document.getElementById('loan_amount').value),
            loan_annuity: parseFloat(document.getElementById('loan_annuity').value),
            goods_price: parseFloat(document.getElementById('goods_price').value),
            num_children: parseInt(document.getElementById('num_children').value),
            education_type: document.getElementById('education_type').value,
            housing_type: document.getElementById('housing_type').value,
            bureau_loans_active: parseInt(document.getElementById('bureau_loans_active').value),
            bureau_overdue_count: parseInt(document.getElementById('bureau_overdue_count').value),
            prev_application_count: parseInt(document.getElementById('prev_application_count').value),
            prev_approved_ratio: parseFloat(document.getElementById('prev_approved_ratio').value),
            external_source_2: parseFloat(document.getElementById('external_source_2').value),
            external_source_3: parseFloat(document.getElementById('external_source_3').value)
        };

        try {
            // Send API call to FastAPI
            const result = await API.post('/predict', payload);
            
            // Render results
            this.renderResults(result);
            
            // Trigger history update if active
            HistoryTab.loadHistory();
        } catch (error) {
            alert(`Lỗi đánh giá tín dụng: ${error.message}`);
            this.resultsEmpty.style.display = 'block';
        } finally {
            this.resultsLoading.style.display = 'none';
            this.btnAssess.disabled = false;
            this.btnAssess.innerHTML = '<i class="fa-solid fa-chart-line"></i> <span>Bắt Đầu Đánh Giá Rủi Ro</span>';
        }
    },

    renderResults(data) {
        // Show content panel
        this.resultsContent.style.display = 'block';

        // 1. Animate Credit Score Ring
        const score = data.credit_score;
        const displayScore = document.getElementById('display-score');
        displayScore.innerText = score;

        // Calculate offset (300 is min, 850 is max. Range is 550)
        const scorePercent = (score - 300) / 550;
        const strokeOffset = this.maxCircumference - (this.maxCircumference * scorePercent);
        
        const ring = document.getElementById('score-ring');
        ring.style.stroke = data.risk_color;
        ring.style.strokeDashoffset = strokeOffset;

        // 2. Set Badge Details
        const badge = document.getElementById('display-badge');
        badge.innerText = data.risk_grade;
        
        // Clean previous classes
        badge.className = 'badge';
        badge.classList.add(`badge-${data.risk_grade.toLowerCase()}`);

        // Set action recommendation
        const actionEl = document.getElementById('display-action');
        actionEl.innerText = this.formatActionName(data.recommended_action);
        actionEl.style.color = data.risk_color;

        const actionDescEl = document.getElementById('display-action-desc');
        actionDescEl.innerText = data.action_description;

        // 3. Render Top Risk Factors List
        const factorsList = document.getElementById('display-factors');
        factorsList.innerHTML = ''; // Clear previous

        data.explanation.top_risk_factors.forEach(factor => {
            const li = document.createElement('li');
            li.style.display = 'flex';
            li.style.alignItems = 'flex-start';
            li.style.gap = '0.5rem';
            li.style.padding = '0.5rem';
            li.style.borderRadius = 'var(--border-radius-sm)';
            li.style.background = 'rgba(255, 255, 255, 0.02)';
            
            // Icon color based on direction
            const isIncrease = factor.direction === 'risk_increase';
            const iconColor = isIncrease ? 'var(--accent-red)' : 'var(--accent-green)';
            const iconClass = isIncrease ? 'fa-solid fa-circle-chevron-up' : 'fa-solid fa-circle-chevron-down';

            li.innerHTML = `
                <i class="${iconClass}" style="color: ${iconColor}; margin-top: 0.2rem;"></i>
                <div>
                    <strong>${factor.display_name}:</strong> 
                    <span style="color: ${iconColor}; font-weight: bold; margin-left: 0.2rem;">${factor.shap_value >= 0 ? '+' : ''}${factor.shap_value.toFixed(3)}</span>
                    <p style="color: var(--text-secondary); font-size: 0.8rem; margin-top: 0.15rem;">${factor.description}</p>
                </div>
            `;
            factorsList.appendChild(li);
        });

        // 4. Load SHAP image (bust browser cache using timestamp)
        const shapImg = document.getElementById('display-shap-img');
        shapImg.src = `${data.explanation.shap_plot_url}?t=${new Date().getTime()}`;
    },

    formatActionName(action) {
        const mapping = {
            'AUTO_APPROVE': 'PHÊ DUYỆT TỰ ĐỘNG',
            'APPROVE_WITH_CONDITIONS': 'DUYỆT CÓ ĐIỀU KIỆN',
            'MANUAL_REVIEW': 'THẨM ĐỊNH THỦ CÔNG',
            'REJECT': 'TỪ CHỐI CHO VAY'
        };
        return mapping[action] || action;
    }
};
