// 1. URL base limpia
// Si el backend se expone mediante el servicio Docker `newsradar_api`, puedes definir
// window.NEWSRADAR_API_URL = 'http://newsradar_api:8000/api/v1' desde el HTML o la configuración.
const API_URL = window.NEWSRADAR_API_URL || '/api/v1'; 

// Traducciones básicas (extensible)
const TRANSLATIONS = {
    es: {
        "nav.dashboard": "Resumen",
        "nav.sources": "Fuentes",
        "nav.alerts": "Alertas",
        "nav.news": "Noticias",
        "nav.logout": "Salir",

        "login.title": "Iniciar sesión",
        "login.note": "Usa el usuario admin para entrar rápidamente.",
        "login.email_label": "Email",
        "login.email_placeholder": "admin@newsradar.com",
        "login.password_label": "Contraseña",
        "login.password_placeholder": "admin123",
        "login.submit": "Iniciar sesión",
        "login.credentials": "Credenciales: admin@newsradar.com / admin123",
        "login.create_account": "Crear cuenta",
        "login.success": "Sesión iniciada",

        "register.title": "Crear cuenta",
        "register.note": "Regístrate para crear alertas y guardar tus preferencias.",
        "register.first_name_label": "Nombre",
        "register.first_name_placeholder": "Nombre",
        "register.last_name_label": "Apellido",
        "register.last_name_placeholder": "Apellido",
        "register.email_label": "Email",
        "register.email_placeholder": "usuario@correo.com",
        "register.password_label": "Contraseña",
        "register.password_placeholder": "Contraseña",
        "register.submit": "Crear cuenta",
        "register.back": "Volver",
        "register.success": "Cuenta creada correctamente. Inicia sesión.",
        "register.fill_required": "Rellena todos los campos obligatorios.",

        "dashboard.title": "Resumen rápido",
        "dashboard.note": "Operaciones principales disponibles al instante.",
        "dashboard.refresh": "Actualizar",

        "stats.sources": "Fuentes",
        "stats.alerts": "Alertas activas",
        "stats.news": "Noticias",
        "stats.api": "API",

        "sources.title": "Fuentes RSS",
        "sources.note": "Agrega y sincroniza tus fuentes de noticias.",
        "sources.new": "+ Nueva fuente",
        "sources.add_title": "Agregar nueva fuente",
        "sources.name_label": "Nombre",
        "sources.name_placeholder": "BBC News",
        "sources.medium_label": "Medio",
        "sources.medium_placeholder": "BBC",
        "sources.url_label": "URL RSS",
        "sources.url_placeholder": "https://...",
        "sources.save": "Guardar",
        "sources.cancel": "Cancelar",
        "sources.created": "Fuente creada",
        "sources.url_required": "La URL es obligatoria",

        "alerts.title": "Alertas",
        "alerts.note": "Configura alertas para tus palabras clave.",
        "alerts.new": "+ Nueva alerta",
        "alerts.create_title": "Crear alerta",
        "alerts.name_label": "Nombre",
        "alerts.name_placeholder": "Alerta tecnología",
        "alerts.keyword_label": "Palabra clave",
        "alerts.keyword_placeholder": "tecnología",
        "alerts.save": "Guardar",
        "alerts.cancel": "Cancelar",
        "alerts.created": "Alerta creada",

        "news.title": "Noticias recientes",
        "news.note": "Noticias extraídas de tus fuentes RSS.",
        "news.refresh": "Actualizar",
        "news.synced": "{count} noticias nuevas sincronizadas",

        "empty.sources": "No hay fuentes cargadas.",
        "empty.alerts": "No hay alertas configuradas.",
        "empty.news": "No hay noticias disponibles.",

        "logout.success": "Sesión cerrada correctamente",
        "session.expired": "Sesión expirada",
        "error.request": "Error en la petición",
    },
    en: {
        "nav.dashboard": "Overview",
        "nav.sources": "Sources",
        "nav.alerts": "Alerts",
        "nav.news": "News",
        "nav.logout": "Logout",

        "login.title": "Sign in",
        "login.note": "Use the admin account to quickly log in.",
        "login.email_label": "Email",
        "login.email_placeholder": "admin@newsradar.com",
        "login.password_label": "Password",
        "login.password_placeholder": "admin123",
        "login.submit": "Sign in",
        "login.credentials": "Credentials: admin@newsradar.com / admin123",
        "login.create_account": "Create account",
        "login.success": "Signed in",

        "register.title": "Create account",
        "register.note": "Register to create alerts and save preferences.",
        "register.first_name_label": "First name",
        "register.first_name_placeholder": "First name",
        "register.last_name_label": "Last name",
        "register.last_name_placeholder": "Last name",
        "register.email_label": "Email",
        "register.email_placeholder": "user@example.com",
        "register.password_label": "Password",
        "register.password_placeholder": "Password",
        "register.submit": "Create account",
        "register.back": "Back",
        "register.success": "Account created successfully. Sign in.",
        "register.fill_required": "Fill all required fields.",

        "dashboard.title": "Quick overview",
        "dashboard.note": "Main operations available instantly.",
        "dashboard.refresh": "Refresh",

        "stats.sources": "Sources",
        "stats.alerts": "Active alerts",
        "stats.news": "News",
        "stats.api": "API",

        "sources.title": "RSS Sources",
        "sources.note": "Add and sync your news sources.",
        "sources.new": "+ New source",
        "sources.add_title": "Add new source",
        "sources.name_label": "Name",
        "sources.name_placeholder": "BBC News",
        "sources.medium_label": "Medium",
        "sources.medium_placeholder": "BBC",
        "sources.url_label": "RSS URL",
        "sources.url_placeholder": "https://...",
        "sources.save": "Save",
        "sources.cancel": "Cancel",
        "sources.created": "Source created",
        "sources.url_required": "URL is required",

        "alerts.title": "Alerts",
        "alerts.note": "Configure alerts for your keywords.",
        "alerts.new": "+ New alert",
        "alerts.create_title": "Create alert",
        "alerts.name_label": "Name",
        "alerts.name_placeholder": "Tech alert",
        "alerts.keyword_label": "Keyword",
        "alerts.keyword_placeholder": "technology",
        "alerts.save": "Save",
        "alerts.cancel": "Cancel",
        "alerts.created": "Alert created",

        "news.title": "Recent news",
        "news.note": "News fetched from your RSS sources.",
        "news.refresh": "Refresh",
        "news.synced": "{count} new items synchronized",

        "empty.sources": "No sources loaded.",
        "empty.alerts": "No alerts configured.",
        "empty.news": "No news available.",

        "logout.success": "Signed out successfully",
        "session.expired": "Session expired",
        "error.request": "Request error",
    }
};

// Gestión de idioma y traducción en DOM
function getTranslation(lang, key) {
    return (TRANSLATIONS[lang] && TRANSLATIONS[lang][key]) || null;
}

const app = {
    token: localStorage.getItem('token'),
    userID: 1, // ID por defecto para las rutas jerárquicas /users/1/...
    currentLang: localStorage.getItem('lang') || (navigator.language && navigator.language.startsWith('en') ? 'en' : 'es'),

    t(key) {
        const tr = getTranslation(this.currentLang, key) || getTranslation('es', key) || getTranslation('en', key);
        return tr || key;
    },

    setLanguage(lang) {
        if (!TRANSLATIONS[lang]) return;
        this.currentLang = lang;
        localStorage.setItem('lang', lang);
        // actualizar todos los selects de idioma (navbar + login/register)
        document.querySelectorAll('.lang-select').forEach(s => { try { s.value = lang; } catch(e){} });
        const nav = document.getElementById('lang-select');
        if (nav) nav.value = lang;
        // actualizar atributo lang del HTML
        try { document.documentElement.lang = lang; } catch (e) {}
        this.translatePage();
    },

    translatePage() {
        // elementos con texto
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const txt = this.t(key);
            if (el.tagName.toLowerCase() === 'input' || el.tagName.toLowerCase() === 'textarea') {
                el.value = txt;
            } else {
                el.textContent = txt;
            }
        });

        // atributos placeholder
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            const txt = this.t(key);
            if (txt) el.setAttribute('placeholder', txt);
        });
    },

    async init() {
        // Aplicar idioma guardado al inicio
        this.setLanguage(this.currentLang);

        // Asegurar que el selector global esté sincronizado (no tocar estilos inline)
        const globalSel = document.getElementById('lang-select');
        if (globalSel) {
            try {
                globalSel.value = this.currentLang;
                // asegurarnos de que use estilos CSS
                globalSel.style.removeProperty('position');
                globalSel.style.removeProperty('top');
                globalSel.style.removeProperty('right');
                globalSel.style.removeProperty('z-index');
            } catch (e) { /* ignore */ }
        }
        // Ocultar cualquier selector local remanente
        document.querySelectorAll('.lang-select').forEach(s => { try { s.style.display = 'none'; } catch(e){} });

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

            this.toast(this.t('login.success'), 'success');
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
        this.toast(this.t('logout.success'));
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

        if (sectionId === 'login' || sectionId === 'register') {
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
            throw new Error(this.t('session.expired') || 'Sesión expirada');
        }
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || this.t('error.request') || 'Error en la petición');
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
            this.toast(err.message || this.t('error.request'), 'error');
        }
    },

    renderSources(sources) {
        const container = document.getElementById('sources-list');
        if (!container) return;

        if (!sources || sources.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>${this.t('empty.sources')}</p>
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
            this.toast(this.t('sources.url_required') || 'La URL es obligatoria', 'error');
            return;
        }

        try {
            await this.fetchAPI('/information-sources', 'POST', {
                name: name || medium || 'Fuente RSS',
                rss_url: url,
                medium,
                iptc_category: category
            });
            this.toast(this.t('sources.created') || 'Fuente creada', 'success');
            this.toggleForm('add-source-form');
            this.clearSourceForm();
            this.loadSources();
        } catch (err) {
            this.toast(err.message || this.t('error.request') || 'Error al crear fuente', 'error');
        }
    },

    // --- REGISTRO ---
    async register(event) {
        event.preventDefault();
        const first_name = document.getElementById('reg-first-name').value.trim();
        const last_name = document.getElementById('reg-last-name').value.trim();
        const email = document.getElementById('reg-email').value.trim();
        const password = document.getElementById('reg-password').value;
        const errorDiv = document.getElementById('register-error');

        errorDiv.textContent = '';

        if (!first_name || !last_name || !email || !password) {
            errorDiv.textContent = this.t('register.fill_required') || 'Rellena todos los campos obligatorios.';
            errorDiv.classList.add('show');
            return;
        }

        try {
            const resp = await fetch(`${API_URL}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password, first_name, last_name })
            });

            if (!resp.ok) {
                const err = await resp.json().catch(() => ({}));
                throw new Error(err.detail || 'Error al registrar usuario');
            }

            this.toast(this.t('register.success') || 'Cuenta creada correctamente. Inicia sesión.', 'success');
            this.showSection('login');
            // Prefill login email
            document.getElementById('login-email').value = email;
            document.getElementById('reg-first-name').value = '';
            document.getElementById('reg-last-name').value = '';
            document.getElementById('reg-email').value = '';
            document.getElementById('reg-password').value = '';
        } catch (err) {
            errorDiv.textContent = err.message || (this.t('error.request') || 'Error al registrar usuario');
            errorDiv.classList.add('show');
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
            this.toast(err.message || this.t('error.request'), 'error');
        }
    },

    renderAlerts(alerts) {
        const container = document.getElementById('alerts-list');
        if (!container) return;

        if (!alerts || alerts.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>${this.t('empty.alerts')}</p>
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
            this.toast(this.t('alerts.created') || 'Alerta creada', 'success');
            this.toggleForm('add-alert-form');
            this.clearAlertForm();
            this.loadAlerts();
        } catch (err) {
            this.toast(err.message || this.t('error.request') || 'Error al crear alerta', 'error');
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
            const news = await this.fetchAPI('/news/latest');
            this.renderNews(news);
        } catch (err) {
            console.error(err);
        }
        try {
            const result = await this.fetchAPI('/news/fetch', 'POST');
            const template = this.t('news.synced');
            const syncedMsg = template ? template.replace('{count}', result.new_items) : `${result.new_items} noticias nuevas sincronizadas`;
            this.toast(syncedMsg, 'success');
            const news = await this.fetchAPI('/news/latest');
            this.renderNews(news);
        } catch (err) {
            console.error(err);
        }
    },

    renderNews(news) {
        const container = document.getElementById('news-list');
        if (!container) return;

        if (!news || news.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>${this.t('empty.news')}</p>
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