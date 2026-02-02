import logging
import time
from typing import List, Optional, Tuple

from django.utils import timezone

from core.helpers import analyze_bill_relevance
from core.models import Bill
from core.utils.scraper import LegisScraper

logger = logging.getLogger(__name__)


def build_measure_id(chamber: str, number: int) -> str:
    """
    Construye ID de medida según convención SUTRA.
    """
    if chamber.upper() == "C":
        return f"P. de la C. {number}"
    elif chamber.upper() == "S":
        return f"P. del S. {number}"
    else:
        raise ValueError(f"Chamber debe ser 'C' o 'S', recibido: {chamber}")


def sync_bill_to_db(measure_id: str, run_ai: bool = True) -> Tuple[Optional[Bill], bool]:
    """
    Sincroniza una medida específica con la base de datos.
    Retorna (Bill, ai_called).
    """
    scraper = LegisScraper()
    bill_data = scraper.scrape_bill(measure_id)
    ai_called = False

    if not bill_data:
        logger.warning(f"No se pudo obtener datos para {measure_id}")
        return None, False

    try:
        bill, created = Bill.objects.update_or_create(
            number=bill_data["number"],
            defaults={
                "title": bill_data["title"],
                "last_updated": timezone.now(),
            },
        )

        if run_ai:
            # Solo analizar si no tiene score o si fue recién creada
            if created or not getattr(bill, "ai_score", 0):
                logger.info(f"🤖 Analizando {bill.number} con IA...")
                result = analyze_bill_relevance(bill)
                ai_called = True
                if result:
                    bill.ai_score = result.get("score", 0)
                    bill.ai_analysis = result.get("analysis", "")
                    bill.relevance_why = (result.get("analysis", "")[:500])
                    bill.save(update_fields=["ai_score", "ai_analysis", "relevance_why"])

        return bill, ai_called
    except Exception as e:
        logger.error(f"Error guardando {measure_id}: {e}")
        return None, False


def sync_bills_range(
    chamber: str, start: int, limit: int, run_ai: bool = True
) -> int:
    """
    Sincroniza un rango de medidas.
    """
    count = 0
    for i in range(start, start + limit):
        measure_id = build_measure_id(chamber, i)
        bill, ai_called = sync_bill_to_db(measure_id, run_ai=run_ai)
        if bill:
            count += 1
        
        # Rate limiting
        time.sleep(10 if ai_called else 1)
    return count


def sync_specific_bills(bill_ids: List[str], run_ai: bool = True) -> int:
    """
    Sincroniza una lista de IDs.
    """
    count = 0
    for measure_id in bill_ids:
        bill, ai_called = sync_bill_to_db(measure_id, run_ai=run_ai)
        if bill:
            count += 1
        
        # Rate limiting
        time.sleep(10 if ai_called else 1)
    return count
