import feedparser

sources = {
    'Primera Hora': [
        'https://www.primerahora.com/feed/',
        'https://www.primerahora.com/rss/',
        'https://www.primerahora.com/arc/outboundfeeds/rss/?outputType=xml',
        'https://www.primerahora.com/noticias/feed/',
    ],
    'El Vocero': [
        'https://www.elvocero.com/feed/',
        'https://www.elvocero.com/rss/',
        'https://www.elvocero.com/arc/outboundfeeds/rss/?outputType=xml',
        'https://www.elvocero.com/noticias/feed/',
    ],
    'NotiCel': [
        'https://www.noticel.com/feed/',
        'https://www.noticel.com/rss/',
        'https://www.noticel.com/arc/outboundfeeds/rss/?outputType=xml',
        'https://www.noticel.com/noticias/feed/',
    ]
}

print("=" * 80)
print("VERIFICACIÓN DE RSS FEEDS - FUENTES DE PUERTO RICO")
print("=" * 80)

for source_name, urls in sources.items():
    print(f"\n📰 {source_name}")
    print("-" * 80)
    
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
            else:
                print(f"❌ {url}")
                print(f"   Status: {status} | Entradas: 0")
        except Exception as e:
            print(f"❌ {url}")
            print(f"   Error: {str(e)}")
    
    print()
