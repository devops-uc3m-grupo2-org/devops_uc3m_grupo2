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

# 10 medios × 10 canales = 100 canales RSS cubriendo las 17 categorías IPTC
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
            ("https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/salud/portada", "Salud"),
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
            ("https://e00-elmundo.uecdn.es/elmundo/rss/tecnologia.xml", "Ciencia y tecnología"),
            ("https://e00-elmundo.uecdn.es/elmundo/rss/cultura.xml", "Artes, cultura, entretenimiento y medios"),
            ("https://e00-elmundo.uecdn.es/elmundo/rss/deportes.xml", "Deporte"),
            ("https://e00-elmundo.uecdn.es/elmundo/rss/salud.xml", "Salud"),
            ("https://e00-elmundo.uecdn.es/elmundo/rss/sociedad.xml", "Sociedad"),
            ("https://e00-elmundo.uecdn.es/elmundo/rss/internacional.xml", "Conflicto, guerra y paz"),
            ("https://e00-elmundo.uecdn.es/elmundo/rss/motor.xml", "Estilo de vida y tiempo libre"),
            ("https://e00-elmundo.uecdn.es/elmundo/rss/cronica.xml", "Policía y justicia"),
        ],
    },
    {
        "name": "ABC",
        "medium": "digital",
        "rss_url": "https://www.abc.es/rss/feeds/abc_ultima_hora.xml",
        "iptc_category": "Política",
        "channels": [
            ("https://www.abc.es/rss/feeds/abc_ultima_hora.xml", "Política"),
            ("https://www.abc.es/rss/feeds/abc_Economia.xml", "Economía, negocios y finanzas"),
            ("https://www.abc.es/rss/feeds/abc_Ciencia.xml", "Ciencia y tecnología"),
            ("https://www.abc.es/rss/feeds/abc_Cultura.xml", "Artes, cultura, entretenimiento y medios"),
            ("https://www.abc.es/rss/feeds/abc_Deportes.xml", "Deporte"),
            ("https://www.abc.es/rss/feeds/abc_Salud.xml", "Salud"),
            ("https://www.abc.es/rss/feeds/abc_Espana.xml", "Sociedad"),
            ("https://www.abc.es/rss/feeds/abc_Familia.xml", "Interés humano, animales, insólito"),
            ("https://www.abc.es/rss/feeds/abc_Religion.xml", "Religión y culto"),
            ("https://www.abc.es/rss/feeds/abc_Internacional.xml", "Conflicto, guerra y paz"),
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
            ("https://www.lavanguardia.com/rss/tendencias.xml", "Estilo de vida y tiempo libre"),
        ],
    },
    {
        "name": "RTVE",
        "medium": "televisión",
        "rss_url": "https://api2.rtve.es/rss/temas/noticias.xml",
        "iptc_category": "Política",
        "channels": [
            ("https://api2.rtve.es/rss/temas/noticias.xml", "Política"),
            ("https://api2.rtve.es/rss/temas/noticias-economia.xml", "Economía, negocios y finanzas"),
            ("https://api2.rtve.es/rss/temas/noticias-ciencia.xml", "Ciencia y tecnología"),
            ("https://api2.rtve.es/rss/temas/noticias-cultura.xml", "Artes, cultura, entretenimiento y medios"),
            ("https://api2.rtve.es/rss/temas/noticias-deportes.xml", "Deporte"),
            ("https://api2.rtve.es/rss/temas/noticias-salud.xml", "Salud"),
            ("https://api2.rtve.es/rss/temas/noticias-sociedad.xml", "Sociedad"),
            ("https://api2.rtve.es/rss/temas/el-tiempo.xml", "Meteorología"),
            ("https://api2.rtve.es/rss/temas/noticias-internacional.xml", "Conflicto, guerra y paz"),
            ("https://api2.rtve.es/rss/temas/noticias-catastrofes.xml", "Catástrofes y accidentes"),
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
            ("https://e00-expansion.uecdn.es/rss/finanzas-personales.xml", "Economía, negocios y finanzas"),
            ("https://e00-expansion.uecdn.es/rss/emprendedores-y-pymes.xml", "Economía, negocios y finanzas"),
            ("https://e00-expansion.uecdn.es/rss/opinion.xml", "Economía, negocios y finanzas"),
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
            ("https://www.20minutos.es/rss/cultura-y-tv/", "Artes, cultura, entretenimiento y medios"),
            ("https://www.20minutos.es/rss/deportes/", "Deporte"),
            ("https://www.20minutos.es/rss/sociedad/", "Sociedad"),
            ("https://www.20minutos.es/rss/salud/", "Salud"),
            ("https://www.20minutos.es/rss/gente-y-tendencias/", "Estilo de vida y tiempo libre"),
            ("https://www.20minutos.es/rss/nacional/", "Interés humano, animales, insólito"),
            ("https://www.20minutos.es/rss/internacional/", "Conflicto, guerra y paz"),
        ],
    },
    {
        "name": "elDiario.es",
        "medium": "digital",
        "rss_url": "https://www.eldiario.es/rss/",
        "iptc_category": "Política",
        "channels": [
            ("https://www.eldiario.es/rss/", "Política"),
            ("https://www.eldiario.es/economia/rss/", "Economía, negocios y finanzas"),
            ("https://www.eldiario.es/sociedad/rss/", "Sociedad"),
            ("https://www.eldiario.es/cultura/rss/", "Artes, cultura, entretenimiento y medios"),
            ("https://www.eldiario.es/internacional/rss/", "Conflicto, guerra y paz"),
            ("https://www.eldiario.es/desigualdad/rss/", "Mano de obra"),
            ("https://www.eldiario.es/medioambiente/rss/", "Medio ambiente"),
            ("https://www.eldiario.es/educacion/rss/", "Educación"),
            ("https://www.eldiario.es/salud/rss/", "Salud"),
            ("https://www.eldiario.es/andalucia/rss/", "Interés humano, animales, insólito"),
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
