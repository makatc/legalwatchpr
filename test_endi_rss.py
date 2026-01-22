import feedparser

urls_to_test = [
    'https://www.elnuevodia.com/rss/',
    'https://www.elnuevodia.com/feed/',
    'https://www.elnuevodia.com/noticias/rss/',
    'https://www.elnuevodia.com/rss/puerto-rico/',
]

print("=== PROBANDO URLS DE EL NUEVO DÍA ===\n")
for url in urls_to_test:
    print(f"📡 Probando: {url}")
    try:
        d = feedparser.parse(url)
        status = getattr(d, 'status', 'N/A')
        entries = len(d.entries)
        title = d.feed.get('title', 'N/A')
        
        print(f"   Status: {status}")
        print(f"   Entries: {entries}")
        print(f"   Title: {title}")
        
        if entries > 0:
            print(f"   ✅ FUNCIONA - Primera entrada: {d.entries[0].get('title', 'Sin título')[:50]}...")
        else:
            print(f"   ❌ NO HAY ENTRADAS")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    print()
