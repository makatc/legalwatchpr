import requests
from bs4 import BeautifulSoup
import urllib3
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class LegisScraper:
    def scrape_bill(self, sutra_id):
        url = f"https://sutra.oslpr.org/medidas/{sutra_id}"
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=20, verify=False)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 1. NÚMERO
                h1_tag = soup.find('h1')
                if h1_tag:
                    full_header = h1_tag.get_text(strip=True)
                    match = re.search(r'\((.*?)\)', full_header)
                    number = match.group(1) if match else full_header[:20]
                else:
                    return None

                # 2. TÍTULO
                title = "Descripción no disponible"
                all_texts = soup.find_all(string=True)
                for text in all_texts:
                    t = text.strip()
                    if (t.startswith("Para ") or t.startswith("Ley ")) and len(t) > 20:
                        title = t
                        break
                if title == "Descripción no disponible":
                    title = full_header

                # 3. ESTATUS
                h2_tag = soup.find('h2')
                status = h2_tag.get_text(strip=True) if h2_tag else "Desconocido"

                # --- 4. NUEVO: COMISIÓN ---
                # Buscamos la frase "Referido a..." o cualquier mención de Comisión
                commission = "Sin asignar"
                
                # Buscamos en todo el texto visible
                body_text = soup.get_text(" ", strip=True)
                
                # Expresión regular para encontrar "Comisión de [Algo]"
                # Busca: Comisión de Salud, Comisión de Hacienda, etc.
                match_com = re.search(r'(Comisión de [A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?: [A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)', body_text)
                
                if match_com:
                    commission = match_com.group(1)
                elif "Referido a" in body_text:
                    # Intento alternativo: buscar la frase cercana a "Referido"
                    try:
                        partes = body_text.split("Referido a")
                        if len(partes) > 1:
                            subparte = partes[1].split('.')[0] # Tomar hasta el punto
                            commission = subparte[:50].strip() # Limitar largo
                    except:
                        pass

                return {
                    'number': number,
                    'title': title,
                    'status': status,
                    'commission': commission, # Enviamos el dato nuevo
                    'sutra_url': url
                }
            
        except Exception as e:
            print(f"Error en ID {sutra_id}: {e}")
            return None
        
        return None