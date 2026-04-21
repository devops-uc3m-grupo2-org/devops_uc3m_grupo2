// 1. URL base limpia
// Si el backend se expone mediante el servicio Docker `newsradar_api`, puedes definir
// window.NEWSRADAR_API_URL = 'http://newsradar_api:8000/api/v1' desde el HTML o la configuración.
const API_URL = window.NEWSRADAR_API_URL || '/api/v1'; 

const app = {
    token: localStorage.getItem('token'),
    userID: 1, // ID por defecto para las rutas jerárquicas /users/1/...

    async init() {
        if (this.token) {
            this.showNavbar();
            this.showSection('dashboard');
            await this.loadDashboardData();
        } else {
            this.hideNavbar();
            this.showSection('login');
        }
    },

    // --- AUTENTICACIÓN ---
    async login(event) {
        event.preventDefault();
        const email = document.getElementById('login-email').value.trim();
        const password = document.getElementById('login-password').value;
        const errorDiv = document.getElementById('login-error');

        try {
            const response = await fetch(`${API_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: email, password: password }),
            });

            if (!response.ok) throw new Error('Credenciales inválidas');

            const data = await response.json();
            this.token = data.access_token;
            localStorage.setItem('token', this.token);

            this.toast('Sesión iniciada', 'success');
            this.showSection('dashboard');
        } catch (err) {
            errorDiv.textContent = err.message;
            errorDiv.classList.add('show');
        }
    },

    logout() {
        this.token = null;
        localStorage.removeItem('token');
        this.hideNavbar();
        this.showSection('login');
        this.toast('Sesión cerrada correctamente');
    },

    showNavbar() {
        document.querySelector('.navbar')?.classList.add('show');
    },

    hideNavbar() {
        document.querySelector('.navbar')?.classList.remove('show');
    },

    // --- NAVEGACIÓN Y UI ---
    showSection(sectionId) {
        // Ocultar todas las secciones
        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
        
        // Mostrar la sección seleccionada
        const section = document.getElementById(sectionId);
        if (section) section.classList.add('active');

        if (sectionId === 'login') {
            this.hideNavbar();
        } else {
            this.showNavbar();
        }

        // Cargar datos automáticamente al cambiar de pestaña
        if (sectionId === 'dashboard') this.loadDashboardData();
        if (sectionId === 'sources') this.loadSources();
        if (sectionId === 'alerts') this.loadAlerts();
        if (sectionId === 'news') this.refreshNews();
    },

    toggleForm(formId) {
        const form = document.getElementById(formId);
        if (form) form.classList.toggle('hidden');
    },

    // --- CARGA Y RENDERIZADO DE DATOS ---
    async loadDashboardData() {
        try {
            const statsList = await this.fetchAPI('/stats');
            const stats = statsList[0] || { metrics: [] };
            this.renderDashboard(stats);
        } catch (err) {
            console.error(err);
        }
    },

    renderDashboard(stats) {
        // Ponemos 0 por defecto si no hay métricas
        let sources = 0, alerts = 0, news = 0;

        if (stats && stats.metrics) {
            stats.metrics.forEach(m => {
                if (m.name === 'total_sources') sources = m.value;
                if (m.name === 'total_alerts') alerts = m.value;
                if (m.name === 'total_news') news = m.value;
            });
        }

        // Pintamos los datos en el HTML
        document.getElementById('stat-sources').textContent = sources;
        document.getElementById('stat-alerts').textContent = alerts;
        document.getElementById('stat-news').textContent = news;
        document.getElementById('stat-health').textContent = 'OK';
    },

    // --- UTILIDADES ---
    async fetchAPI(endpoint, method = 'GET', body = null) {
        const options = { 
            method, 
            headers: { 'Accept': 'application/json' } 
        };
        
        if (body) {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(body);
        }
        if (this.token) {
            options.headers['Authorization'] = `Bearer ${this.token}`;
        }

        const response = await fetch(`${API_URL}${endpoint}`, options);
        
        if (response.status === 401) {
            this.logout();
            throw new Error('Sesión expirada');
        }
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || 'Error en la petición');
        }
        
        return response.json();
    },

    toast(message, type = 'info') {
        console.log(`[${type.toUpperCase()}] ${message}`);
        const container = document.getElementById('toast-container');
        if (container) {
            const toastEl = document.createElement('div');
            toastEl.style.padding = '10px';
            toastEl.style.background = type === 'error' ? 'red' : 'green';
            toastEl.style.color = 'white';
            toastEl.style.marginTop = '5px';
            toastEl.textContent = message;
            container.appendChild(toastEl);
            setTimeout(() => toastEl.remove(), 3000);
        }
    },

    // --- FUENTES ---
    async loadSources() {
        try {
            const sources = await this.fetchAPI('/information-sources');
            this.renderSources(sources);
        } catch (err) {
            console.error(err);
            this.toast('Error al cargar fuentes', 'error');
        }
    },

    renderSources(sources) {
        const container = document.getElementById('sources-list');
        if (!container) return;

        if (!sources || sources.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>No hay fuentes cargadas.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = sources.map(source => `
            <div class="card source-card">
                <div class="source-header">
                    <strong>${source.name || 'Fuente'}</strong>
                    <span>${source.rss_url || source.url || ''}</span>
                </div>
            </div>
        `).join('');
    },

    async createSource(e) {
        e.preventDefault();
        const name = document.getElementById('source-name').value.trim();
        const medium = document.getElementById('source-medium').value.trim();
        const url = document.getElementById('source-rss-url').value.trim();
        const category = document.getElementById('source-iptc').value || null;

        if (!url) {
            this.toast('La URL es obligatoria', 'error');
            return;
        }

        try {
            await this.fetchAPI('/information-sources', 'POST', {
                name: name || medium || 'Fuente RSS',
                rss_url: url,
                medium,
                iptc_category: category
            });
            this.toast('Fuente creada', 'success');
            this.toggleForm('add-source-form');
            this.clearSourceForm();
            this.loadSources();
        } catch (err) {
            this.toast(err.message || 'Error al crear fuente', 'error');
        }
    },

    clearSourceForm() {
        document.getElementById('source-name').value = '';
        document.getElementById('source-medium').value = '';
        document.getElementById('source-rss-url').value = '';
        document.getElementById('source-iptc').value = '';
    },

    // --- ALERTAS Y NOTICIAS ---
    async loadAlerts() {
        try {
            const alerts = await this.fetchAPI(`/users/${this.userID}/alerts`);
            this.renderAlerts(alerts);
        } catch (err) {
            console.error(err);
            this.toast('Error al cargar alertas', 'error');
        }
    },

    renderAlerts(alerts) {
        const container = document.getElementById('alerts-list');
        if (!container) return;

        if (!alerts || alerts.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>No hay alertas definidas.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = alerts.map(alert => `
            <div class="card alert-card">
                <div class="source-header">
                    <strong>${alert.name}</strong>
                    <span>${alert.cron_expression}</span>
                </div>
                <p>${alert.descriptors?.join(', ') || ''}</p>
                <p>Categoria: ${alert.categories?.map(c => c.label).join(', ') || ''}</p>
            </div>
        `).join('');
    },

    async createAlert(e) {
        e.preventDefault();
        const name = document.getElementById('alert-name').value.trim();
        const keyword = document.getElementById('alert-keyword').value.trim();
        const synonyms = document.getElementById('alert-synonyms').value.split(',').map(s => s.trim()).filter(Boolean);
        const iptcCategory = document.getElementById('alert-iptc').value;
        const cronExpression = document.getElementById('alert-cron').value.trim();
        const userId = parseInt(document.getElementById('alert-user-id').value) || this.userID;

        if (!name || !keyword || !iptcCategory || !cronExpression) {
            this.toast('Rellena todos los campos obligatorios (nombre, keyword, categoría y cron)', 'error');
            return;
        }

        const categories = [{ code: iptcCategory, label: iptcCategory }];
        const descriptors = [keyword, ...synonyms];

        try {
            await this.fetchAPI(`/users/${userId}/alerts`, 'POST', {
                name,
                descriptors,
                categories,
                cron_expression: cronExpression,
                is_active: true
            });
            this.toast('Alerta creada', 'success');
            this.toggleForm('add-alert-form');
            this.clearAlertForm();
            this.loadAlerts();
        } catch (err) {
            this.toast(err.message || 'Error al crear alerta', 'error');
        }
    },

    clearAlertForm() {
        document.getElementById('alert-name').value = '';
        document.getElementById('alert-keyword').value = '';
        document.getElementById('alert-synonyms').value = '';
        document.getElementById('alert-iptc').value = '';
        document.getElementById('alert-cron').value = '';
    },

    async refreshNews() {
        try {
            const result = await this.fetchAPI('/news/fetch', 'POST');
            this.toast(`${result.new_items} noticias nuevas sincronizadas`, 'success');
            const news = await this.fetchAPI('/news/latest');
            this.renderNews(news);
        } catch (err) {
            console.error(err);
            this.toast(err.message || 'Error al cargar noticias', 'error');
        }
    },

    renderNews(news) {
        const container = document.getElementById('news-list');
        if (!container) return;

        if (!news || news.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>No hay noticias disponibles.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = news
            .map(item => `
                <article class="card news-card">
                    <div class="news-header">
                        <a href="${item.link}" target="_blank" rel="noopener noreferrer">
                            <h3>${item.title}</h3>
                        </a>
                        <div class="news-meta">
                            <span>${item.source_name || 'Fuente desconocida'}</span>
                            <span>${item.category_name || 'Sin categoría'}</span>
                            <span>${item.published ? new Date(item.published).toLocaleString() : ''}</span>
                        </div>
                    </div>
                    <p>${item.summary || ''}</p>
                    <div class="news-footer">
                        <small>Canal: <a href="${item.channel_url}" target="_blank" rel="noopener noreferrer">${item.channel_url}</a></small>
                    </div>
                </article>
            `)
            .join('');
    }
};

// Iniciar app

// Iniciar app
document.addEventListener('DOMContentLoaded', () => app.init());