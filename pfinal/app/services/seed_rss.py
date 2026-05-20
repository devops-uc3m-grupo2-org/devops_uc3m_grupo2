from app.models.models import InformationSource, RSSChannel, Category, IPTCCategoryEnum

IPTC_CATALOG = {
    "01000000": "Artes, cultura, entretenimiento y medios",
    "02000000": "Policía y justicia",
    "03000000": "Catástrofes y accidentes",
    "04000000": "Economía, negocios y finanzas",
    "05000000": "Educación",
    "06000000": "Medio ambiente",
    "07000000": "Salud",
    "08000000": "Interés humano, animales, insólito",
    "09000000": "Mano de obra",
    "10000000": "Estilo de vida y tiempo libre",
    "11000000": "Política",
    "12000000": "Religión y culto",
    "13000000": "Ciencia y tecnología",
    "14000000": "Sociedad",
    "15000000": "Deporte",
    "16000000": "Conflicto, guerra y paz",
    "17000000": "Meteorología",
}
IPTC_NAME_TO_ID = {name.casefold(): int(code) for code, name in IPTC_CATALOG.items()}

SEED_SOURCES = [
    {
        "name": "El País",
        "medium": "digital",
        "rss_url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada",
        "iptc_category": "Política",
        "channels": [
            ("https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada", "Política"),
            ("https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/economia/portada", "Economía, negocios y finanzas"),
            ("https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/ciencia/portada", "Ciencia y tecnología"),
            ("https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/cultura/portada", "Artes, cultura, entretenimiento y medios"),
            ("https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/deportes/portada", "Deporte"),
            ("https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/sociedad/portada", "Sociedad"),
            ("https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/espana/portada", "Política"),
            ("https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/clima-y-medio-ambiente/portada", "Medio ambiente"),
            ("https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional/portada", "Conflicto, guerra y paz"),
            ("https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/educacion/portada", "Educación"),
        ],
    },
    {
        "name": "El Mundo",
        "medium": "digital",
        "rss_url": "https://e00-elmundo.uecdn.es/elmundo/rss/portada.xml",
        "iptc_category": "Política",
        "channels": [
            ("https://e00-elmundo.uecdn.es/elmundo/rss/portada.xml", "Política"),
            ("https://e00-elmundo.uecdn.es/elmundo/rss/economia.xml", "Economía, negocios y finanzas"),
            ("https://e00-elmundo.uecdn.es/elmundo/rss/cultura.xml", "Artes, cultura, entretenimiento y medios"),
            ("https://e00-elmundo.uecdn.es/elmundo/rss/internacional.xml", "Conflicto, guerra y paz"),
            ("https://www.elmundo.es/rss/tecnologia.xml", "Ciencia y tecnología"),
            ("https://www.elmundo.es/rss/deportes.xml", "Deporte"),
            ("https://www.elmundo.es/rss/salud.xml", "Salud"),
            ("https://www.elmundo.es/rss/sociedad.xml", "Sociedad"),
            ("https://www.elmundo.es/rss/motor.xml", "Estilo de vida y tiempo libre"),
            ("https://www.elmundo.es/rss/cronica.xml", "Interés humano, animales, insólito"),
        ],
    },
    {
        "name": "ABC",
        "medium": "digital",
        "rss_url": "https://www.abc.es/rss/feeds/abc_Espana.xml",
        "iptc_category": "Política",
        "channels": [
            ("https://www.abc.es/rss/feeds/abc_Espana.xml", "Política"),
            ("https://www.abc.es/rss/feeds/abc_Economia.xml", "Economía, negocios y finanzas"),
            ("https://www.abc.es/rss/feeds/abc_Ciencia.xml", "Ciencia y tecnología"),
            ("https://www.abc.es/rss/feeds/abc_Cultura.xml", "Artes, cultura, entretenimiento y medios"),
            ("https://www.abc.es/rss/feeds/abc_Deportes.xml", "Deporte"),
            ("https://www.abc.es/rss/feeds/abc_Internacional.xml", "Conflicto, guerra y paz"),
            ("https://www.abc.es/rss/feeds/abc_Familia.xml", "Interés humano, animales, insólito"),
            ("https://www.abc.es/rss/feeds/abc_Religion.xml", "Religión y culto"),
        ],
    },
    {
        "name": "La Vanguardia",
        "medium": "digital",
        "rss_url": "https://www.lavanguardia.com/rss/home.xml",
        "iptc_category": "Política",
        "channels": [
            ("https://www.lavanguardia.com/rss/home.xml", "Política"),
            ("https://www.lavanguardia.com/rss/economia.xml", "Economía, negocios y finanzas"),
            ("https://www.lavanguardia.com/rss/ciencia.xml", "Ciencia y tecnología"),
            ("https://www.lavanguardia.com/rss/cultura.xml", "Artes, cultura, entretenimiento y medios"),
            ("https://www.lavanguardia.com/rss/deportes.xml", "Deporte"),
            ("https://www.lavanguardia.com/rss/salud.xml", "Salud"),
            ("https://www.lavanguardia.com/rss/vida.xml", "Sociedad"),
            ("https://www.lavanguardia.com/rss/medioambiente.xml", "Medio ambiente"),
            ("https://www.lavanguardia.com/rss/internacional.xml", "Conflicto, guerra y paz"),
            ("https://www.lavanguardia.com/rss/motor.xml", "Estilo de vida y tiempo libre"),
        ],
    },
    {
        "name": "Euronews España",
        "medium": "televisión",
        "rss_url": "https://es.euronews.com/rss",
        "iptc_category": "Política",
        "channels": [
            ("https://es.euronews.com/rss", "Política"),
            ("https://es.euronews.com/rss?level=theme&name=news", "Sociedad"),
            ("https://es.euronews.com/rss?level=theme&name=business", "Economía, negocios y finanzas"),
            ("https://es.euronews.com/rss?level=theme&name=sport", "Deporte"),
            ("https://es.euronews.com/rss?level=theme&name=weather", "Meteorología"),
        ],
    },
    {
        "name": "Expansión",
        "medium": "digital",
        "rss_url": "https://e00-expansion.uecdn.es/rss/portada.xml",
        "iptc_category": "Economía, negocios y finanzas",
        "channels": [
            ("https://e00-expansion.uecdn.es/rss/portada.xml", "Economía, negocios y finanzas"),
            ("https://e00-expansion.uecdn.es/rss/mercados.xml", "Economía, negocios y finanzas"),
            ("https://e00-expansion.uecdn.es/rss/empresas.xml", "Economía, negocios y finanzas"),
            ("https://e00-expansion.uecdn.es/rss/economia-politica.xml", "Economía, negocios y finanzas"),
            ("https://e00-expansion.uecdn.es/rss/ahorro.xml", "Economía, negocios y finanzas"),
            ("https://e00-expansion.uecdn.es/rss/tecnologia.xml", "Ciencia y tecnología"),
            ("https://e00-expansion.uecdn.es/rss/empleo.xml", "Mano de obra"),
            ("https://e00-expansion.uecdn.es/rss/opinion.xml", "Economía, negocios y finanzas"),
            ("https://e00-expansion.uecdn.es/rss/juridico.xml", "Policía y justicia"),
            ("https://e00-expansion.uecdn.es/rss/catalunya.xml", "Política"),
        ],
    },
    {
        "name": "Marca",
        "medium": "digital",
        "rss_url": "https://e00-marca.uecdn.es/rss/portada.xml",
        "iptc_category": "Deporte",
        "channels": [
            ("https://e00-marca.uecdn.es/rss/portada.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/baloncesto.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/tenis.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/motor.xml", "Estilo de vida y tiempo libre"),
            ("https://e00-marca.uecdn.es/rss/ciclismo.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/golf.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/atletismo.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/boxeo.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/padel.xml", "Deporte"),
        ],
    },
    {
        "name": "El Confidencial",
        "medium": "digital",
        "rss_url": "https://rss.elconfidencial.com/espana/",
        "iptc_category": "Política",
        "channels": [
            ("https://rss.elconfidencial.com/espana/", "Política"),
            ("https://rss.elconfidencial.com/mercados/", "Economía, negocios y finanzas"),
            ("https://rss.elconfidencial.com/tecnologia/", "Ciencia y tecnología"),
            ("https://rss.elconfidencial.com/cultura/", "Artes, cultura, entretenimiento y medios"),
            ("https://rss.elconfidencial.com/deportes/", "Deporte"),
            ("https://rss.elconfidencial.com/sociedad/", "Sociedad"),
            ("https://rss.elconfidencial.com/mundo/", "Conflicto, guerra y paz"),
            ("https://rss.elconfidencial.com/empresas/", "Economía, negocios y finanzas"),
            ("https://rss.elconfidencial.com/tendencias/", "Estilo de vida y tiempo libre"),
            ("https://rss.elconfidencial.com/ultima-hora-nacional/", "Policía y justicia"),
        ],
    },
    {
        "name": "20 Minutos",
        "medium": "digital",
        "rss_url": "https://www.20minutos.es/rss/",
        "iptc_category": "Política",
        "channels": [
            ("https://www.20minutos.es/rss/", "Política"),
            ("https://www.20minutos.es/rss/economia/", "Economía, negocios y finanzas"),
            ("https://www.20minutos.es/rss/tecnologia/", "Ciencia y tecnología"),
            ("https://www.20minutos.es/rss/deportes/", "Deporte"),
            ("https://www.20minutos.es/rss/salud/", "Salud"),
            ("https://www.20minutos.es/rss/nacional/", "Política"),
            ("https://www.20minutos.es/rss/internacional/", "Conflicto, guerra y paz"),
            ("https://www.20minutos.es/rss/ciencia/", "Ciencia y tecnología"),
            ("https://www.20minutos.es/rss/motor/", "Estilo de vida y tiempo libre"),
            ("https://www.20minutos.es/rss/medio-ambiente/", "Medio ambiente"),
        ],
    },
    {
        "name": "elDiario.es",
        "medium": "digital",
        "rss_url": "https://www.eldiario.es/rss/",
        "iptc_category": "Política",
        "channels": [
            ("https://www.eldiario.es/rss/", "Política"),
        ],
    },
    {
        "name": "BBC Mundo",
        "medium": "digital",
        "rss_url": "https://feeds.bbci.co.uk/mundo/rss.xml",
        "iptc_category": "Política",
        "channels": [
            ("https://feeds.bbci.co.uk/mundo/rss.xml", "Política"),
            ("https://feeds.bbci.co.uk/mundo/noticias/america_latina/rss.xml", "Política"),
            ("https://feeds.bbci.co.uk/mundo/noticias/internacional/rss.xml", "Conflicto, guerra y paz"),
            ("https://feeds.bbci.co.uk/mundo/noticias/economia/rss.xml", "Economía, negocios y finanzas"),
            ("https://feeds.bbci.co.uk/mundo/noticias/ciencia_tecnologia/rss.xml", "Ciencia y tecnología"),
            ("https://feeds.bbci.co.uk/mundo/noticias/salud/rss.xml", "Salud"),
            ("https://feeds.bbci.co.uk/mundo/noticias/cultura/rss.xml", "Artes, cultura, entretenimiento y medios"),
            ("https://feeds.bbci.co.uk/mundo/noticias/deportes/rss.xml", "Deporte"),
            ("https://feeds.bbci.co.uk/mundo/noticias/medio_ambiente/rss.xml", "Medio ambiente"),
            ("https://feeds.bbci.co.uk/mundo/noticias/sociedad/rss.xml", "Sociedad"),
        ],
    },
    {
        "name": "El Español",
        "medium": "digital",
        "rss_url": "https://www.elespanol.com/rss/",
        "iptc_category": "Política",
        "channels": [
            ("https://www.elespanol.com/rss/", "Política"),
        ],
    },
    {
        "name": "Mundo Deportivo",
        "medium": "digital",
        "rss_url": "https://www.mundodeportivo.com/feed/rss/home",
        "iptc_category": "Deporte",
        "channels": [
            ("https://www.mundodeportivo.com/feed/rss/home", "Deporte"),
            ("https://www.mundodeportivo.com/feed/rss/futbol", "Deporte"),
            ("https://www.mundodeportivo.com/feed/rss/futbol/internacional", "Deporte"),
            ("https://www.mundodeportivo.com/feed/rss/baloncesto", "Deporte"),
            ("https://www.mundodeportivo.com/feed/rss/motor", "Estilo de vida y tiempo libre"),
            ("https://www.mundodeportivo.com/feed/rss/motor/f1", "Estilo de vida y tiempo libre"),
            ("https://www.mundodeportivo.com/feed/rss/tenis", "Deporte"),
            ("https://www.mundodeportivo.com/feed/rss/futbol/champions-league", "Deporte"),
            ("https://www.mundodeportivo.com/feed/rss/futbol/premier-league", "Deporte"),
            ("https://www.mundodeportivo.com/feed/rss/futbol/serie-a", "Deporte"),
            ("https://www.mundodeportivo.com/feed/rss/futbol/bundesliga", "Deporte"),
            ("https://www.mundodeportivo.com/feed/rss/futbol/europa-league", "Deporte"),
            ("https://www.mundodeportivo.com/feed/rss/rugby", "Deporte"),
            ("https://www.mundodeportivo.com/feed/rss/boxeo", "Deporte"),
            ("https://www.mundodeportivo.com/feed/rss/atletismo", "Deporte"),
        ],
    },
    {
        "name": "Cinco Días",
        "medium": "digital",
        "rss_url": "https://feeds.elpais.com/mrss-s/pages/ep/site/cincodias.elpais.com/portada",
        "iptc_category": "Economía, negocios y finanzas",
        "channels": [
            ("https://feeds.elpais.com/mrss-s/pages/ep/site/cincodias.elpais.com/portada", "Economía, negocios y finanzas"),
            ("https://feeds.elpais.com/mrss-s/list/ep/site/elpais.com/section/opinion", "Política"),
            ("https://feeds.elpais.com/mrss-s/list/ep/site/elpais.com/section/babelia", "Artes, cultura, entretenimiento y medios"),
            ("https://feeds.elpais.com/mrss-s/list/ep/site/elpais.com/section/eps", "Sociedad"),
            ("https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/tecnologia/portada", "Ciencia y tecnología"),
        ],
    },
    {
        # Misma fuente que La Vanguardia — el seed reutiliza el InformationSource existente
        "name": "La Vanguardia",
        "medium": "digital",
        "rss_url": "https://www.lavanguardia.com/rss/home.xml",
        "iptc_category": "Política",
        "channels": [
            ("https://www.lavanguardia.com/rss/politica.xml", "Política"),
            ("https://www.lavanguardia.com/rss/opinion.xml", "Política"),
            ("https://www.lavanguardia.com/rss/gente.xml", "Interés humano, animales, insólito"),
            ("https://www.lavanguardia.com/rss/sucesos.xml", "Policía y justicia"),
            ("https://www.lavanguardia.com/rss/participacion.xml", "Sociedad"),
            ("https://www.lavanguardia.com/rss/lacontra.xml", "Sociedad"),
            ("https://www.lavanguardia.com/rss/natural.xml", "Medio ambiente"),
            ("https://www.lavanguardia.com/rss/vida/salud.xml", "Salud"),
            ("https://www.lavanguardia.com/rss/tecnologia.xml", "Ciencia y tecnología"),
            ("https://www.lavanguardia.com/rss/local/catalunya.xml", "Política"),
            ("https://www.lavanguardia.com/rss/local/paisvasco.xml", "Política"),
            ("https://www.lavanguardia.com/rss/local/valencia.xml", "Política"),
            ("https://www.lavanguardia.com/rss/local/sevilla.xml", "Política"),
            ("https://www.lavanguardia.com/rss/local/madrid.xml", "Política"),
            ("https://www.lavanguardia.com/rss/local/girona.xml", "Política"),
            ("https://www.lavanguardia.com/rss/local/lleida.xml", "Política"),
            ("https://www.lavanguardia.com/rss/local/tarragona.xml", "Política"),
            ("https://www.lavanguardia.com/rss/local/barcelona.xml", "Política"),
            ("https://www.lavanguardia.com/rss/comer.xml", "Estilo de vida y tiempo libre"),
            ("https://www.lavanguardia.com/rss/mascotas.xml", "Interés humano, animales, insólito"),
            ("https://www.lavanguardia.com/rss/vivo.xml", "Sociedad"),
            ("https://www.lavanguardia.com/rss/magazine.xml", "Sociedad"),
            ("https://www.lavanguardia.com/rss/series.xml", "Artes, cultura, entretenimiento y medios"),
            ("https://www.lavanguardia.com/rss/television.xml", "Artes, cultura, entretenimiento y medios"),
            ("https://www.lavanguardia.com/rss/mamas-y-papas.xml", "Interés humano, animales, insólito"),
            ("https://www.lavanguardia.com/rss/ocio/viajes.xml", "Estilo de vida y tiempo libre"),
        ],
    },
    {
        # Misma fuente que Marca — el seed reutiliza el InformationSource existente
        "name": "Marca",
        "medium": "digital",
        "rss_url": "https://e00-marca.uecdn.es/rss/portada.xml",
        "iptc_category": "Deporte",
        "channels": [
            ("https://e00-marca.uecdn.es/rss/futbol/primera-division.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/segunda-division.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/mas-futbol.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/copa-rey.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/seleccion.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/futbol-sala.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/futbol-internacional.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/champions-league.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/europa-league.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/premier-league.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/bundesliga.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/liga-francesa.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/mundial-de-clubes.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/america.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/real-madrid.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/barcelona.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/atletico.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/sevilla.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/athletic.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/villarreal.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/real-sociedad.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/betis.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/celta.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/osasuna.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/mallorca.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/alaves.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/getafe.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/rayo.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/levante.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/leganes.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/girona.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/las-palmas.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/tenerife.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/elche.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/malaga.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/deportivo.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/zaragoza.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/sporting.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/oviedo.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/racing-santander.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/lugo.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/mirandes.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/fuenlabrada.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/alcorcon.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/numancia.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/ponferradina.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/eibar.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/futbol/granada.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/baloncesto/nba.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/baloncesto/copa-rey.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/baloncesto/basketfeb.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/baloncesto/acb.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/motor/formula1.xml", "Estilo de vida y tiempo libre"),
        ],
    },
    {
        # Misma fuente que Mundo Deportivo — el seed reutiliza el InformationSource existente
        "name": "Mundo Deportivo",
        "medium": "digital",
        "rss_url": "https://www.mundodeportivo.com/feed/rss/home",
        "iptc_category": "Deporte",
        "channels": [
            ("https://www.mundodeportivo.com/feed/rss/futbol/ligue-1", "Deporte"),
            ("https://www.mundodeportivo.com/feed/rss/elotromundo", "Sociedad"),
            ("https://www.mundodeportivo.com/feed/rss/ufc", "Deporte"),
            ("https://www.mundodeportivo.com/feed/rss/beisbol", "Deporte"),
        ],
    },
    {
        "name": "Sport España",
        "medium": "digital",
        "rss_url": "https://www.sport.es/es/rss/last-news/news.xml",
        "iptc_category": "Deporte",
        "channels": [
            ("https://www.sport.es/es/rss/last-news/news.xml", "Deporte"),
            ("https://e00-marca.uecdn.es/rss/en/index.xml", "Deporte"),
        ],
    },
]


def seed_rss_channels(db):
    for source_data in SEED_SOURCES:
        try:
            source = db.query(InformationSource).filter(
                InformationSource.rss_url == source_data["rss_url"]
            ).first()
            if not source:
                source = InformationSource(
                    name=source_data["name"],
                    medium=source_data["medium"],
                    rss_url=source_data["rss_url"],
                    iptc_category=source_data["iptc_category"],
                )
                db.add(source)
                db.commit()
                db.refresh(source)

            for channel_url, category_name in source_data["channels"]:
                try:
                    category_id = IPTC_NAME_TO_ID.get(category_name.casefold())
                    category = db.query(Category).filter(Category.id == category_id).first() if category_id else None
                    if not category:
                        category = Category(id=category_id, name=category_name, source="IPTC")
                        db.add(category)
                        db.commit()
                        db.refresh(category)

                    channel = db.query(RSSChannel).filter(RSSChannel.url == channel_url).first()
                    if channel:
                        if channel.category_id != (category.id if category else None):
                            channel.category_id = category.id if category else None
                            db.add(channel)
                        continue

                    if category:
                        db.add(RSSChannel(
                            url=channel_url,
                            information_source_id=source.id,
                            category_id=category.id,
                        ))
                except Exception:
                    db.rollback()

            db.commit()
        except Exception:
            db.rollback()
