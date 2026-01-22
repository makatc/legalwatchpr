import feedparser

sources = {
    'Microjuris': [
        'https://www.microjuris.com/feed/',
        'https://www.microjuris.com/rss/',
        'https://microjuris.com/feed/',
    ],
    'Indice PR': [
        'https://www.indicempr.com/feed/',
        'https://www.indicempr.com/rss/',
        'https://indicempr.com/feed/',
    ],
    'Centro de Periodismo Investigativo': [
        'https://periodismoinvestigativo.com/feed/',
        'https://www.periodismoinvestigativo.com/feed/',
        'https://periodismoinvestigativo.com/rss/',
    ],
    'Telemundo PR': [
        'https://www.telemundopr.com/feed/',
        'https://www.telemundopr.com/noticias/feed/',
        'https://www.telemundopr.com/rss/',
        'https://telemundopr.com/feed/',
    ],
    'WAPA Noticias': [
        'https://www.wapa.tv/feed/',
        'https://www.wapa.tv/noticias/feed/',
        'https://www.wapa.tv/rss/',
        'https://wapa.tv/feed/',
    ],
    'NotiUno': [
        'https://www.notiuno.com/feed/',
        'https://www.notiuno.com/rss/',
        'https://notiuno.com/feed/',
    ],
    'Caribbean Business': [
        'https://caribbeanbusiness.com/feed/',
        'https://www.caribbeanbusiness.com/feed/',
        'https://caribbeanbusiness.com/rss/',
    ],
}

print("=" * 80)
print("VERIFICACIÓN DE RSS FEEDS - FUENTES ADICIONALES PUERTO RICO")
print("=" * 80)

for source_name, urls in sources.items():
    print(f"\n📰 {source_name}")
    print("-" * 80)
    
    found_working = False
    for url in urls:
        try:
            feed = feedparser.parse(url)
            status = feed.get('status', 'N/A')
            entries = len(feed.entries)
            
            if entries > 0:
                print(f"✅ {url}")
                print(f"   Status: {status} | Entradas: {entries}")
                print(f"   Primeros 2 títulos:")
                for entry in feed.entries[:2]:
                    print(f"   - {entry.title}")
                print()
                found_working = True
                break  # Ya encontramos uno que funciona
            else:
                print(f"❌ {url}")
                print(f"   Status: {status} | Entradas: 0")
        except Exception as e:
            print(f"❌ {url}")
            print(f"   Error: {str(e)}")
    
    if not found_working:
        print(f"   ⚠️  No se encontró feed RSS funcional para {source_name}")
    
    print()
