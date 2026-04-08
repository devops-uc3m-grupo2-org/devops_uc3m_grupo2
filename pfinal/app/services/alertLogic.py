def match_alert(alert, news_item):

    text = (news_item.title + " " + (news_item.summary or "")).lower()

    #Creamos lista con la palabra clave y los sinonimos de la alerta
    keywords = [alert.keyword.lower()] + [  
        s.lower() for s in alert.get_synonyms()
    ]
    # Recorremos cada palabra del text y vemos si es una de la "clave", devuelve True si encontramos una
    return any(k in text for k in keywords)