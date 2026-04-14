const API_URL = 'http://localhost:8000/api/v1';

// Global app state
const app = {
    token: localStorage.getItem('token') || null,
    currentUser: null,

    async init() {
        // Check if token exists and try to load user
        if (this.token) {
            this.showSection('dashboard');
            this.loadDashboardData();
        } else {
            this.showSection('login-section');
        }
    },

    // Auth Functions
    async login(event) {
        event.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        const errorDiv = document.getElementById('login-error');

        try {
            errorDiv.classList.remove('show');
            const formData = new FormData();
            formData.append('username', email);
            formData.append('password', password);

            const response = await fetch(`${API_URL}/auth/login`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Credenciales inválidas');
            }

            const data = await response.json();
            this.token = data.access_token;
            localStorage.setItem('token', this.token);

            this.currentUser = { email };
            this.toast('Sesión iniciada correctamente', 'success');
            this.showSection('dashboard');
            this.loadDashboardData();

            // Clear form
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
        this.currentUser = null;
        this.showSection('login-section');
        this.toast('Sesión cerrada', 'success');
    },

    // Section Navigation
    showSection(sectionId) {
        // Hide all sections
        document.querySelectorAll('.section').forEach(s => {
            s.classList.remove('active');
        });

        // Show selected section
        const section = document.getElementById(sectionId + '-section');
        if (section) {
            section.classList.add('active');
        }

        // Handle navbar visibility
        const navbar = document.querySelector('.navbar');
        if (sectionId === 'login-section') {
            navbar.classList.remove('show');
        } else {
            navbar.classList.add('show');
        }

        // Load data based on section
        if (sectionId === 'sources') this.loadSources();
        if (sectionId === 'alerts') this.loadAlerts();
        if (sectionId === 'news') this.loadNews();
    },

    // Dashboard
    async loadDashboardData() {
        try {
            const health = await this.fetchAPI(`/health`);
            const sources = await this.fetchAPI('/sources');
            const alerts = await this.fetchAPI('/alerts');
            const news = await this.fetchAPI('/news');

            document.getElementById('stat-health').textContent = health.status === 'ok' ? '✅ OK' : '❌ Error';
            document.getElementById('stat-sources').textContent = sources.length;
            document.getElementById('stat-alerts').textContent = alerts.filter(a => a.is_active).length;
            document.getElementById('stat-news').textContent = news.length;
        } catch (error) {
            console.error('Error loading dashboard:', error);
            this.toast('Error al cargar el dashboard', 'error');
        }
    },

    // Sources Management
    async loadSources() {
        try {
            const sources = await this.fetchAPI('/sources');
            const container = document.getElementById('sources-list');

            if (sources.length === 0) {
                container.innerHTML = '<div class="empty-state"><p>No hay fuentes configuradas. ¡Crea una nueva!</p></div>';
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
                        <strong>URL:</strong> <a href="${source.rss_url}" target="_blank">Ver Feed</a><br>
                        <strong>Categoría:</strong> ${this.escapeHtml(source.iptc_category || 'N/A')}<br>
                        <strong>ID:</strong> ${source.id}
                    </div>
                    <div class="card-actions">
                        <button class="btn btn-secondary" onclick="app.fetchSourceNews(${source.id})">
                            📥 Sincronizar
                        </button>
                        <button class="btn btn-secondary" onclick="app.fetchSourceDebug(${source.id})">
                            🔍 Debug
                        </button>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Error loading sources:', error);
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
            this.toast('Fuente creada exitosamente', 'success');
            this.toggleForm('add-source');
            this.loadSources();

            // Reset form
            event.target.reset();
        } catch (error) {
            this.toast('Error al crear fuente: ' + error.message, 'error');
        }
    },

    async fetchSourceNews(sourceId) {
        try {
            const result = await this.fetchAPI(`/sources/${sourceId}/fetch`);
            this.toast(`✅ ${result.new_items} nuevas noticias sincronizadas`, 'success');
            this.loadDashboardData();
        } catch (error) {
            this.toast('Error al sincronizar: ' + error.message, 'error');
        }
    },

    async fetchSourceDebug(sourceId) {
        try {
            const result = await this.fetchAPI(`/sources/${sourceId}/fetch?debug=true`);
            const msg = `📡 Feed Status: ${result.feed_status}\n📰 Total entries: ${result.entries_count}`;
            alert(msg);
        } catch (error) {
            this.toast('Error en debug: ' + error.message, 'error');
        }
    },

    // Alerts Management
    async loadAlerts() {
        try {
            const alerts = await this.fetchAPI('/alerts');
            const container = document.getElementById('alerts-list');

            if (alerts.length === 0) {
                container.innerHTML = '<div class="empty-state"><p>No hay alertas configuradas. ¡Crea una nueva!</p></div>';
                return;
            }

            container.innerHTML = alerts.map(alert => `
                <div class="card">
                    <div class="card-header">
                        <div>
                            <div class="card-title">${this.escapeHtml(alert.name)}</div>
                            <div class="card-subtitle">Palabra clave: ${this.escapeHtml(alert.keyword)}</div>
                        </div>
                        <span class="card-status ${alert.is_active ? 'active' : 'inactive'}">
                            ${alert.is_active ? '🟢 Activa' : '🔴 Inactiva'}
                        </span>
                    </div>
                    <div class="card-body">
                        <strong>Sinónimos:</strong> ${this.escapeHtml(alert.synonyms.join(', ') || 'Ninguno')}<br>
                        <strong>Categoría:</strong> ${this.escapeHtml(alert.iptc_category || 'N/A')}<br>
                        <strong>ID:</strong> ${alert.id}
                    </div>
                    <div class="card-actions">
                        <button class="btn btn-secondary" onclick="app.toggleAlertStatus(${alert.id}, ${!alert.is_active})">
                            ${alert.is_active ? '⏸ Desactivar' : '▶ Activar'}
                        </button>
                        <button class="btn btn-secondary" onclick="app.deleteAlert(${alert.id})">
                            🗑 Eliminar
                        </button>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Error loading alerts:', error);
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
                    .map(s => s.trim())
                    .filter(s => s),
                iptc_category: document.getElementById('alert-iptc').value,
                cron_expression: document.getElementById('alert-cron').value,
                user_id: parseInt(document.getElementById('alert-user-id').value),
            };

            await this.fetchAPI('/alerts', 'POST', payload);
            this.toast('Alerta creada exitosamente', 'success');
            this.toggleForm('add-alert');
            this.loadAlerts();

            // Reset form
            event.target.reset();
        } catch (error) {
            this.toast('Error al crear alerta: ' + error.message, 'error');
        }
    },

    async toggleAlertStatus(alertId, isActive) {
        try {
            await this.fetchAPI(`/alerts/${alertId}`, 'PUT', { is_active: isActive });
            this.toast(isActive ? 'Alerta activada' : 'Alerta desactivada', 'success');
            this.loadAlerts();
        } catch (error) {
            this.toast('Error al actualizar alerta: ' + error.message, 'error');
        }
    },

    async deleteAlert(alertId) {
        if (confirm('¿Estás seguro de eliminar esta alerta?')) {
            try {
                await this.fetchAPI(`/alerts/${alertId}`, 'DELETE');
                this.toast('Alerta eliminada', 'success');
                this.loadAlerts();
            } catch (error) {
                this.toast('Error al eliminar alerta: ' + error.message, 'error');
            }
        }
    },

    async getSuggestions() {
        const keyword = document.getElementById('alert-keyword').value;
        if (!keyword) {
            this.toast('Por favor ingresa una palabra clave', 'warning');
            return;
        }

        try {
            const data = await this.fetchAPI(`/suggestions?keyword=${encodeURIComponent(keyword)}`);
            const suggestions = data.suggestions.join(', ');
            document.getElementById('alert-synonyms').value = suggestions;
            document.getElementById('synonym-suggestions').textContent = `✨ Sugerencias IA: ${suggestions}`;
        } catch (error) {
            this.toast('Error al obtener sugerencias: ' + error.message, 'error');
        }
    },

    // News Management
    async loadNews() {
        try {
            const news = await this.fetchAPI('/news');
            const container = document.getElementById('news-list');

            if (news.length === 0) {
                container.innerHTML = '<div class="empty-state"><p>No hay noticias disponibles</p></div>';
                return;
            }

            container.innerHTML = news.map(item => `
                <div class="news-item">
                    <div class="news-item-title">
                        <a href="${item.link}" target="_blank">${this.escapeHtml(item.title)}</a>
                    </div>
                    <div class="news-item-meta">
                        <span>📅 ${new Date(item.published).toLocaleDateString()}</span>
                        <span class="news-item-source">Fuente ID: ${item.source_id}</span>
                    </div>
                    <div class="news-item-summary">
                        ${this.escapeHtml(item.summary ? item.summary.substring(0, 300) : 'Sin resumen')}...
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Error loading news:', error);
            this.toast('Error al cargar noticias', 'error');
        }
    },

    async refreshNews() {
        this.loadNews();
        this.toast('Noticias actualizadas', 'success');
    },

    // Actions
    async runMatching() {
        try {
            await this.fetchAPI('/run-matching', 'POST');
            this.toast('✅ Matching ejecutado correctamente', 'success');
            this.loadDashboardData();
        } catch (error) {
            this.toast('Error en matching: ' + error.message, 'error');
        }
    },

    async runScheduler() {
        try {
            await this.fetchAPI('/run-scheduler', 'POST');
            this.toast('✅ Scheduler ejecutado correctamente', 'success');
            this.loadDashboardData();
        } catch (error) {
            this.toast('Error en scheduler: ' + error.message, 'error');
        }
    },

    // UI Helpers
    toggleForm(formId) {
        const form = document.getElementById(formId + '-form');
        if (form) {
            form.classList.toggle('hidden');
        }
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

        setTimeout(() => {
            toast.remove();
        }, 3000);
    },

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    // API Communication
    async fetchAPI(endpoint, method = 'GET', body = null) {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
        };

        if (this.token) {
            options.headers['Authorization'] = `Bearer ${this.token}`;
        }

        if (body) {
            options.body = JSON.stringify(body);
        }

        const response = await fetch(`${API_URL}${endpoint}`, options);

        if (response.status === 401) {
            this.logout();
            throw new Error('No autorizado');
        }

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP Error: ${response.status}`);
        }

        return response.json();
    },
};

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('NewsRadar app initializing...');
    app.init();
});
