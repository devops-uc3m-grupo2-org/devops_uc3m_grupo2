const API_URL = '/api/v1';

const app = {
    token: localStorage.getItem('token'),

    async init() {
        if (this.token) {
            this.showSection('dashboard');
            await this.loadDashboardData();
        } else {
            this.showSection('login');
        }
    },

    async login(event) {
        event.preventDefault();
        const email = document.getElementById('login-email').value.trim();
        const password = document.getElementById('login-password').value;
        const errorDiv = document.getElementById('login-error');

        errorDiv.classList.remove('show');
        errorDiv.textContent = '';

        try {
            const payload = new URLSearchParams();
            payload.append('username', email);
            payload.append('password', password);

            const response = await fetch(`${API_URL}/auth/login`, {
                method: 'POST',
                body: payload,
            });

            if (!response.ok) {
                throw new Error('Credenciales inválidas');
            }

            const data = await response.json();
            this.token = data.access_token;
            localStorage.setItem('token', this.token);

            this.toast('Sesión iniciada', 'success');
            this.showSection('dashboard');
            await this.loadDashboardData();
            document.getElementById('login-email').value = '';
            document.getElementById('login-password').value = '';
        } catch (error) {
            errorDiv.textContent = error.message;
            errorDiv.classList.add('show');
        }
    },

    logout() {
        this.token = null;
        localStorage.removeItem('token');
        this.showSection('login');
        this.toast('Sesión cerrada', 'success');
    },

    showSection(sectionId) {
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });

        const section = document.getElementById(`${sectionId}-page`);
        if (section) {
            section.classList.add('active');
        }

        const navbar = document.querySelector('.navbar');
        if (sectionId === 'login') {
            navbar.classList.remove('show');
        } else {
            navbar.classList.add('show');
        }

        if (sectionId === 'dashboard') {
            this.loadDashboardData();
        }
        if (sectionId === 'sources') {
            this.loadSources();
        }
        if (sectionId === 'alerts') {
            this.loadAlerts();
        }
        if (sectionId === 'news') {
            this.loadNews();
        }
    },

    async loadDashboardData() {
        try {
            const [health, sources, alerts, news] = await Promise.all([
                this.fetchAPI('/health'),
                this.fetchAPI('/sources'),
                this.fetchAPI('/alerts'),
                this.fetchAPI('/news'),
            ]);

            document.getElementById('stat-health').textContent = health.status === 'ok' ? '✅ OK' : '❌ Error';
            document.getElementById('stat-sources').textContent = sources.length;
            document.getElementById('stat-alerts').textContent = alerts.filter(a => a.is_active).length;
            document.getElementById('stat-news').textContent = news.length;
        } catch (error) {
            console.error('Dashboard error:', error);
            this.toast('Error al cargar el resumen', 'error');
        }
    },

    async loadSources() {
        try {
            const sources = await this.fetchAPI('/sources');
            const container = document.getElementById('sources-list');
            if (!sources.length) {
                container.innerHTML = '<div class="empty-state"><p>No hay fuentes cargadas.</p></div>';
                return;
            }

            container.innerHTML = sources.map(source => `
                <div class="card">
                    <div class="card-header">
                        <div>
                            <div class="card-title">${this.escapeHtml(source.name)}</div>
                            <div class="card-subtitle">${this.escapeHtml(source.medium)}</div>
                        </div>
                    </div>
                    <div class="card-body">
                        <strong>URL:</strong> <a href="${this.escapeHtml(source.rss_url)}" target="_blank">Ver feed</a><br>
                        <strong>Categoría:</strong> ${this.escapeHtml(source.iptc_category || 'N/A')}<br>
                        <strong>ID:</strong> ${source.id}
                    </div>
                    <div class="card-actions">
                        <button class="btn btn-secondary" onclick="app.fetchSourceNews(${source.id})">Sincronizar</button>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Sources error:', error);
            this.toast('Error al cargar fuentes', 'error');
        }
    },

    async createSource(event) {
        event.preventDefault();
        try {
            const payload = {
                name: document.getElementById('source-name').value,
                medium: document.getElementById('source-medium').value,
                rss_url: document.getElementById('source-rss-url').value,
                iptc_category: document.getElementById('source-iptc').value,
            };

            await this.fetchAPI('/sources', 'POST', payload);
            this.toast('Fuente creada', 'success');
            this.toggleForm('add-source');
            document.querySelector('#add-source-form form').reset();
            this.loadSources();
        } catch (error) {
            console.error('Create source error:', error);
            this.toast('No se pudo crear la fuente', 'error');
        }
    },

    async fetchSourceNews(sourceId) {
        try {
            const result = await this.fetchAPI(`/sources/${sourceId}/fetch`, 'POST');
            this.toast(`${result.new_items} noticias sincronizadas`, 'success');
            this.loadDashboardData();
        } catch (error) {
            console.error('Fetch news error:', error);
            this.toast('Error al sincronizar fuente', 'error');
        }
    },

    async loadAlerts() {
        try {
            const alerts = await this.fetchAPI('/alerts');
            const container = document.getElementById('alerts-list');
            if (!alerts.length) {
                container.innerHTML = '<div class="empty-state"><p>No hay alertas configuradas.</p></div>';
                return;
            }

            container.innerHTML = alerts.map(alert => `
                <div class="card">
                    <div class="card-header">
                        <div>
                            <div class="card-title">${this.escapeHtml(alert.name)}</div>
                            <div class="card-subtitle">${this.escapeHtml(alert.keyword)}</div>
                        </div>
                        <span class="card-status ${alert.is_active ? 'active' : 'inactive'}">${alert.is_active ? 'Activa' : 'Inactiva'}</span>
                    </div>
                    <div class="card-body">
                        <strong>Sinónimos:</strong> ${this.escapeHtml(alert.synonyms.join(', ') || 'Ninguno')}<br>
                        <strong>Categoría:</strong> ${this.escapeHtml(alert.iptc_category || 'N/A')}<br>
                        <strong>ID:</strong> ${alert.id}
                    </div>
                    <div class="card-actions">
                        <button class="btn btn-secondary" onclick="app.toggleAlertStatus(${alert.id}, ${!alert.is_active})">${alert.is_active ? 'Desactivar' : 'Activar'}</button>
                        <button class="btn btn-secondary" onclick="app.deleteAlert(${alert.id})">Eliminar</button>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Alerts error:', error);
            this.toast('Error al cargar alertas', 'error');
        }
    },

    async createAlert(event) {
        event.preventDefault();
        try {
            const payload = {
                name: document.getElementById('alert-name').value,
                keyword: document.getElementById('alert-keyword').value,
                synonyms: document.getElementById('alert-synonyms').value
                    .split(',')
                    .map(item => item.trim())
                    .filter(Boolean),
                iptc_category: document.getElementById('alert-iptc').value,
                cron_expression: document.getElementById('alert-cron').value,
                user_id: Number(document.getElementById('alert-user-id').value),
            };

            await this.fetchAPI('/alerts', 'POST', payload);
            this.toast('Alerta creada', 'success');
            this.toggleForm('add-alert');
            document.querySelector('#add-alert-form form').reset();
            this.loadAlerts();
        } catch (error) {
            console.error('Create alert error:', error);
            this.toast('No se pudo crear la alerta', 'error');
        }
    },

    async toggleAlertStatus(alertId, isActive) {
        try {
            await this.fetchAPI(`/alerts/${alertId}`, 'PUT', { is_active: isActive });
            this.toast(isActive ? 'Alerta activada' : 'Alerta desactivada', 'success');
            this.loadAlerts();
        } catch (error) {
            console.error('Toggle alert error:', error);
            this.toast('Error al actualizar la alerta', 'error');
        }
    },

    async deleteAlert(alertId) {
        if (!confirm('¿Eliminar esta alerta?')) return;
        try {
            await this.fetchAPI(`/alerts/${alertId}`, 'DELETE');
            this.toast('Alerta eliminada', 'success');
            this.loadAlerts();
        } catch (error) {
            console.error('Delete alert error:', error);
            this.toast('Error al eliminar la alerta', 'error');
        }
    },

    async loadNews() {
        try {
            const news = await this.fetchAPI('/news');
            const container = document.getElementById('news-list');
            if (!news.length) {
                container.innerHTML = '<div class="empty-state"><p>No hay noticias disponibles.</p></div>';
                return;
            }

            container.innerHTML = news.map(item => `
                <article class="news-item">
                    <h3 class="news-item-title"><a href="${this.escapeHtml(item.link)}" target="_blank">${this.escapeHtml(item.title)}</a></h3>
                    <div class="news-item-meta">
                        <span>📅 ${item.published ? new Date(item.published).toLocaleString() : 'Sin fecha'}</span>
                        <span class="news-item-source">Fuente ID: ${item.source_id}</span>
                    </div>
                    <p class="news-item-summary">${this.escapeHtml(item.summary || 'Sin resumen')}</p>
                </article>
            `).join('');
        } catch (error) {
            console.error('News error:', error);
            this.toast('Error al cargar noticias', 'error');
        }
    },

    refreshNews() {
        this.loadNews();
        this.toast('Noticias actualizadas', 'success');
    },

    toggleForm(formId) {
        const form = document.getElementById(`${formId}-form`);
        if (form) form.classList.toggle('hidden');
    },

    toast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        const icons = {
            success: '✓',
            error: '✗',
            warning: '⚠',
            info: 'ⓘ',
        };
        toast.innerHTML = `<span>${icons[type]}</span><span>${message}</span>`;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    },

    escapeHtml(value) {
        if (value === null || value === undefined) return '';
        const div = document.createElement('div');
        div.textContent = String(value);
        return div.innerHTML;
    },

    async fetchAPI(endpoint, method = 'GET', body = null) {
        const options = { method, headers: {} };
        if (body !== null) {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(body);
        }
        if (this.token) {
            options.headers['Authorization'] = `Bearer ${this.token}`;
        }

        const response = await fetch(`${API_URL}${endpoint}`, options);
        if (response.status === 401) {
            this.logout();
            throw new Error('No autorizado');
        }
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }
        return response.json();
    },
};

window.addEventListener('DOMContentLoaded', () => {
    app.init();
});
