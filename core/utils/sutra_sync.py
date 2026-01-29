"""
SUTRA Legislature Scraper
=========================

Scraper para el Sistema Unificado de Trámite Legislativo (SUTRA) de Puerto Rico.

SUTRA es un sistema antiguo con SSL débil y estructura HTML inconsistente.
Este scraper usa requests + BeautifulSoup4 con estrategia de "Direct ID Fetch".

Uso:
    from core.utils.sutra_sync import sync_sutra_bills
    
    # Sincronizar últimas 20 medidas
    sync_sutra_bills(limit=20)
"""

import logging
import re
import time
from typing import Dict, List, Optional

import requests
import urllib3
from bs4 import BeautifulSoup
from django.utils import timezone

from core.models import Bill

# Suprimir advertencias de SSL (SUTRA tiene certificados antiguos)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


# Patrones de URL de SUTRA (actualizar según estructura real)
SUTRA_BASE_URL = "https://sutra.oslpr.org"
SUTRA_MEASURE_URL = f"{SUTRA_BASE_URL}/osl/esutra/MedidaReg.aspx"


def clean_text(text: str) -> str:
    """Limpia texto eliminando espacios extra y saltos de línea."""
    if not text:
        return ""
    # Reemplazar múltiples espacios/saltos con uno solo
    cleaned = re.sub(r'\s+', ' ', text)
    return cleaned.strip()


def build_measure_id(chamber: str, number: int) -> str:
    """
    Construye ID de medida según convención SUTRA.
    
    Args:
        chamber: 'C' para Cámara, 'S' para Senado
        number: Número de la medida
    
    Returns:
        ID formateado (ej: "P. de la C. 1001")
    """
    if chamber.upper() == 'C':
        return f"P. de la C. {number}"
    elif chamber.upper() == 'S':
        return f"P. del S. {number}"
    else:
        raise ValueError(f"Chamber debe ser 'C' o 'S', recibido: {chamber}")


def fetch_bill_from_sutra(measure_id: str) -> Optional[Dict]:
    """
    Obtiene datos de una medida específica desde SUTRA.
    
    Args:
        measure_id: ID de la medida (ej: "P. de la C. 1001")
    
    Returns:
        Diccionario con datos de la medida, o None si falla
    """
    try:
        # Estrategia: usar parámetros de búsqueda directos
        # NOTA: La URL exacta puede variar; ajustar según inspección real de SUTRA
        params = {
            'NroMedida': measure_id,
        }
        
        logger.debug(f"Fetching {measure_id} from SUTRA...")
        
        response = requests.get(
            SUTRA_MEASURE_URL,
            params=params,
            verify=False,  # SUTRA tiene problemas SSL
            timeout=15,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; LegalWatchPR/1.0)'}
        )
        
        if response.status_code != 200:
            logger.warning(f"HTTP {response.status_code} para {measure_id}")
            return None
        
        # Parsear HTML con BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # NOTA: Los selectores CSS/XPath dependen de la estructura real de SUTRA.
        # A continuación, selectores genéricos que deben ajustarse según inspección.
        
        # Buscar título (común: <span id="lblTitulo"> o similar)
        title_elem = soup.find('span', id=re.compile(r'.*[Tt]itulo.*'))
        title = clean_text(title_elem.get_text()) if title_elem else measure_id
        
        # Si no encontramos título específico, intentar con header o bold text
        if not title or title == measure_id:
            title_elem = soup.find('h2') or soup.find('strong')
            title = clean_text(title_elem.get_text()) if title_elem else f"Medida {measure_id}"
        
        # Buscar autores
        authors_elem = soup.find('span', id=re.compile(r'.*[Aa]utor.*'))
        authors = clean_text(authors_elem.get_text()) if authors_elem else ""
        
        # Buscar estado/trámite
        status_elem = soup.find('span', id=re.compile(r'.*[Ee]stado.*|.*[Tt]ramite.*'))
        status = clean_text(status_elem.get_text()) if status_elem else "Desconocido"
        
        # Si encontramos datos válidos, retornar
        if title and title != measure_id:
            logger.info(f"✅ Obtenido: {measure_id} - {title[:50]}...")
            return {
                'number': measure_id,
                'title': title,
                'authors': authors,
                'status': status,
            }
        else:
            logger.warning(f"No se encontró información válida para {measure_id}")
            return None
    
    except requests.exceptions.Timeout:
        logger.error(f"Timeout al obtener {measure_id}")
        return None
    except Exception as e:
        logger.error(f"Error al obtener {measure_id}: {e}")
        return None


def sync_sutra_bills(limit: int = 20, chamber: str = 'C', start_number: int = 1000) -> int:
    """
    Sincroniza medidas desde SUTRA a la base de datos.
    
    Estrategia: Intenta obtener medidas consecutivas desde start_number.
    
    Args:
        limit: Número máximo de medidas a intentar obtener
        chamber: 'C' para Cámara, 'S' para Senado
        start_number: Número inicial de medida
    
    Returns:
        Número de medidas sincronizadas exitosamente
    """
    logger.info(f"\n--- 📋 INICIANDO SINCRONIZACIÓN SUTRA ---")
    logger.info(f"Cámara: {'Cámara' if chamber == 'C' else 'Senado'}")
    logger.info(f"Rango: {start_number} - {start_number + limit - 1}")
    
    synced_count = 0
    attempted = 0
    
    for offset in range(limit):
        number = start_number + offset
        measure_id = build_measure_id(chamber, number)
        
        attempted += 1
        logger.info(f"[{attempted}/{limit}] Procesando {measure_id}...")
        
        # Obtener datos de SUTRA
        bill_data = fetch_bill_from_sutra(measure_id)
        
        if not bill_data:
            logger.info(f"  ⏭️ Saltando {measure_id} (no encontrado o inválido)")
            # Pequeña pausa para no saturar el servidor
            time.sleep(0.5)
            continue
        
        # Guardar en base de datos
        try:
            bill, created = Bill.objects.update_or_create(
                number=bill_data['number'],
                defaults={
                    'title': bill_data['title'],
                    # Campos opcionales que se pueden expandir:
                    # 'authors': bill_data.get('authors', ''),
                    # 'status': bill_data.get('status', ''),
                }
            )
            
            action = "creado" if created else "actualizado"
            logger.info(f"  ✅ {measure_id} {action}")
            synced_count += 1
        
        except Exception as e:
            logger.error(f"  ❌ Error guardando {measure_id}: {e}")
        
        # Pausa entre requests para ser amable con el servidor
        time.sleep(1)
    
    logger.info(f"\n--- FIN SINCRONIZACIÓN ---")
    logger.info(f"Total sincronizadas: {synced_count}/{attempted}")
    
    return synced_count


def sync_specific_bills(bill_ids: List[str]) -> int:
    """
    Sincroniza una lista específica de IDs de medidas.
    
    Args:
        bill_ids: Lista de IDs (ej: ["P. de la C. 1001", "P. del S. 250"])
    
    Returns:
        Número de medidas sincronizadas
    """
    logger.info(f"\n--- 📋 SINCRONIZACIÓN ESPECÍFICA DE {len(bill_ids)} MEDIDAS ---")
    
    synced_count = 0
    
    for measure_id in bill_ids:
        logger.info(f"Procesando {measure_id}...")
        
        bill_data = fetch_bill_from_sutra(measure_id)
        
        if not bill_data:
            logger.warning(f"  ⏭️ No se pudo obtener {measure_id}")
            continue
        
        try:
            bill, created = Bill.objects.update_or_create(
                number=bill_data['number'],
                defaults={'title': bill_data['title']}
            )
            
            action = "creado" if created else "actualizado"
            logger.info(f"  ✅ {measure_id} {action}")
            synced_count += 1
        
        except Exception as e:
            logger.error(f"  ❌ Error guardando {measure_id}: {e}")
        
        time.sleep(1)
    
    logger.info(f"\n--- FIN SINCRONIZACIÓN ESPECÍFICA ---")
    logger.info(f"Total: {synced_count}/{len(bill_ids)}")
    
    return synced_count
