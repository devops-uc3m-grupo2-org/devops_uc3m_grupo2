def match_alert(alert, news_item):
    text = (news_item.title + " " + (news_item.summary or "")).lower()
    keywords = [d.lower() for d in (alert.descriptors or [])]
    return any(k in text for k in keywords)
