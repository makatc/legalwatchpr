import requests
import urllib3
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand

# Desactivar la advertencia de seguridad (Para que no llene la pantalla de alertas)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Command(BaseCommand):
    help = 'Prueba de conexión con SUTRA (Modo Inseguro SSL)'

    def handle(self, *args, **options):
        self.stdout.write("--- INICIANDO PRUEBA DEL ROBOT (VERSIÓN 2) ---")

        # 1. Definimos la URL (Medida P. del S. 794 - ID 159112)
        test_id = 159112
        url = f"https://sutra.oslpr.org/medidas/{test_id}"
        
        self.stdout.write(f"Conectando a: {url} ...")

        # 2. Hacemos la petición
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            # AQUI ESTÁ EL CAMBIO: verify=False le dice que ignore el certificado malo
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            
            # Verificar si respondió bien
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS("¡Conexión Exitosa! (Saltando SSL)"))
                
                # 3. Leemos el HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Intentamos sacar el título
                page_title = soup.title.string.strip() if soup.title else "Sin título"
                self.stdout.write(f"Título detectado: {page_title}")

                # Intentamos buscar pistas de que estamos en la página correcta
                # Buscamos si aparece la palabra "Medida" o el número "794" en el texto
                texto_pag = soup.get_text()
                if "794" in texto_pag or "Medida" in texto_pag:
                     self.stdout.write(self.style.SUCCESS("CONFIRMADO: Vemos información de la medida en el texto."))
                else:
                     self.stdout.write(self.style.WARNING("OJO: Entramos, pero no veo el número 794. Tal vez la estructura cambió."))

            else:
                self.stdout.write(self.style.ERROR(f"Error: SUTRA respondió código {response.status_code}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error fatal: {e}"))