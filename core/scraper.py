import re
import logging

import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class LegisScraper:
    """
    Scraper for SUTRA OSLPR legislative measures.
    Handles robust ID normalization and data extraction.
    """
    
    def __init__(self):
        self.base_url = "https://sutra.oslpr.org/medidas"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def normalize_measure_id(self, measure_id):
        """
        Normalize measure ID for SUTRA URL construction.
        Examples:
            'PC160071' -> 'pc160071'
            'P. de la C. 1234' -> 'pc1234'
            '160071' -> '160071' (keep as-is for numeric IDs)
            'PS0979' -> 'ps0979'
        """
        clean_id = str(measure_id).lower()
        clean_id = clean_id.replace('p. de la c.', 'pc')
        clean_id = clean_id.replace(' ', '').replace('.', '')
        return clean_id
    
    def scrape_bill(self, measure_id):
        """
        Scrape a bill page for measure_id.
        Returns None on 404 or failure.
        Returns dict with 'number' and 'title' keys on success.
        """
        # Normalize the ID for URL construction
        normalized_id = self.normalize_measure_id(measure_id)
        url = f"{self.base_url}/{normalized_id}"
        
        logger.info(f"Scraping {url} for measure {measure_id}")
        
        try:
            response = self.session.get(url, timeout=20, verify=False)
            
            # Check status codes first
            if response.status_code == 404:
                logger.info(f"scrape_bill: {measure_id} returned 404 at {url}")
                return None
            
            if response.status_code != 200:
                logger.warning(f"scrape_bill: {measure_id} unexpected status {response.status_code}")
                return None
            
            # Status is 200, parse content
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
                'commission': commission,
                'sutra_url': url
            }

        except requests.Timeout:
            logger.error(f"Timeout scraping {measure_id}")
            return None
        except requests.RequestException as e:
            logger.error(f"Request error for {measure_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error scraping {measure_id}: {e}", exc_info=True)
            return None