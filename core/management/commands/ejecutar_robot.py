import time
import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Bill, BillEvent, Keyword, MonitoredMeasure, MonitoredCommission, UserProfile
from core.scraper import LegisScraper 

class Command(BaseCommand):
    help = 'Robot Multi-Bot: Clasifica alertas y usa canales específicos'

    def handle(self, *args, **options):
        self.stdout.write("--- 🤖 ROBOT CLASIFICADOR INICIADO ---")

        # 1. CARGAR CONFIGURACIONES
        keywords = list(Keyword.objects.values_list('term', flat=True))
        my_measures = list(MonitoredMeasure.objects.values_list('sutra_id', flat=True))
        my_commissions = list(MonitoredCommission.objects.filter(is_active=True).values_list('name', flat=True))

        # 2. CARGAR CANALES (WEBHOOKS)
        profile = UserProfile.objects.first()
        if not profile:
            self.stdout.write("⚠️ No hay perfil de usuario configurado.")
            return

        # 3. RANGO DE BÚSQUEDA
        last_bill = Bill.objects.order_by('-sutra_id').first()
        start_id = int(last_bill.sutra_id) + 1 if last_bill and last_bill.sutra_id.isdigit() else 152550
        ids_to_scan = list(range(start_id, start_id + 5))

        scraper = LegisScraper()
        
        self.stdout.write(f"🔎 Escaneando desde ID: {ids_to_scan[0]}")

        for current_id in ids_to_scan:
            try:
                data = scraper.scrape_bill(current_id)
                
                if data:
                    sutra_id_str = str(current_id)
                    found_something = False
                    
                    # --- ANÁLISIS DE RUTAS (ROUTING) ---
                    
                    # RUTA 1: MEDIDAS ESPECÍFICAS
                    if data['number'] in my_measures or sutra_id_str in my_measures:
                        self.enviar_discord(profile.webhook_measures, data, "🎯 Medida Rastreada", 10181046) # Morado
                        found_something = True

                    # RUTA 2: COMISIONES
                    if data.get('commission') in my_commissions:
                        self.enviar_discord(profile.webhook_commissions, data, f"🏛️ Actividad en Comisión", 15844367) # Dorado
                        found_something = True

                    # RUTA 3: PALABRAS CLAVE
                    title_lower = data['title'].lower()
                    matched_words = [w for w in keywords if w.lower() in title_lower]
                    if matched_words:
                        razon = f"🔑 Palabras: {', '.join(matched_words)}"
                        self.enviar_discord(profile.webhook_keywords, data, razon, 3066993) # Verde
                        found_something = True

                    # GUARDAR EN BD
                    if found_something:
                        Bill.objects.update_or_create(
                            sutra_id=sutra_id_str,
                            defaults={
                                'number': data['number'],
                                'title': data['title'],
                                'status': data['status'],
                                'commission': data.get('commission', 'Sin asignar'),
                                'sutra_url': data['sutra_url'],
                                'last_updated': timezone.now()
                            }
                        )
                        self.stdout.write(self.style.SUCCESS(f"   ★ {data['number']}: Procesada y enviada a canales correspondientes."))
                    else:
                        self.stdout.write(f"   . {data['number']} ignorada (No coincide con filtros)")

                else:
                    self.stdout.write(f"   . Casilla {current_id} vacía")

            except Exception as e:
                self.stdout.write(f"Error en {current_id}: {e}")
            
            time.sleep(1)

        self.stdout.write("--- ✅ BARRIDO COMPLETADO ---")

    def enviar_discord(self, webhook_url, data, titulo_razon, color_hex):
        """Envía la alerta al webhook específico si existe"""
        if not webhook_url: return

        payload = {
            "embeds": [{
                "title": f"{titulo_razon}: {data['number']}",
                "description": data['title'][:250] + "...",
                "url": data['sutra_url'],
                "color": color_hex,
                "fields": [
                    {"name": "Estatus Actual", "value": data['status'], "inline": True},
                    {"name": "Comisión", "value": data.get('commission', 'N/A'), "inline": True}
                ],
                "footer": {"text": "LegalWatch Multi-Channel Bot"}
            }]
        }
        try:
            requests.post(webhook_url, json=payload)
        except: pass