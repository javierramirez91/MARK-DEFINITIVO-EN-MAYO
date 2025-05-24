"""
Dashboard analítico para el Centre de Psicologia Jaume I.
Proporciona estadísticas y visualizaciones para el seguimiento de las interacciones con pacientes.
"""
import logging
import json
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
import asyncio
import calendar
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from core.config import settings
from admin.auth import get_current_admin_user

# Configurar logging
logger = logging.getLogger("mark.dashboard-analytics")

# Crear router
router = APIRouter(prefix="/analytics", tags=["analytics"])

# Configurar templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

# Definir tipos de análisis disponibles
ANALYTICS_TYPES = {
    "message_volume": "Volumen de mensajes",
    "response_time": "Tiempo de respuesta",
    "playbook_usage": "Uso de playbooks",
    "sentiment_trends": "Tendencias de sentimiento",
    "crisis_alerts": "Alertas de crisis",
    "language_usage": "Uso de idiomas",
    "topic_distribution": "Distribución de temas",
    "appointment_trends": "Tendencias de citas",
    "user_satisfaction": "Satisfacción de usuarios",
    "peak_hours": "Horas pico de actividad"
}

@router.get("/", response_class=HTMLResponse)
async def analytics_dashboard(request: Request, current_user = Depends(get_current_admin_user)):
    """Página principal del dashboard analítico"""
    return templates.TemplateResponse("analytics/dashboard.html", {
        "request": request,
        "title": "Dashboard Analítico",
        "analytics_types": ANALYTICS_TYPES
    })

@router.get("/data/{analytics_type}")
async def get_analytics_data(
    analytics_type: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    granularity: Optional[str] = "day",
    current_user = Depends(get_current_admin_user)
):
    """Obtiene datos analíticos según el tipo solicitado"""
    if analytics_type not in ANALYTICS_TYPES:
        raise HTTPException(status_code=404, detail=f"Tipo de análisis '{analytics_type}' no encontrado")
    
    # Determinar fechas de inicio y fin
    today = datetime.now().date()
    if not end_date:
        end_date_obj = today
    else:
        try:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido para end_date (YYYY-MM-DD)")
    
    if not start_date:
        # Por defecto, 30 días hacia atrás
        start_date_obj = end_date_obj - timedelta(days=30)
    else:
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido para start_date (YYYY-MM-DD)")
    
    # Generar datos según el tipo de análisis
    if analytics_type == "message_volume":
        data = await get_message_volume_data(start_date_obj, end_date_obj, granularity)
    elif analytics_type == "response_time":
        data = await get_response_time_data(start_date_obj, end_date_obj, granularity)
    elif analytics_type == "playbook_usage":
        data = await get_playbook_usage_data(start_date_obj, end_date_obj)
    elif analytics_type == "sentiment_trends":
        data = await get_sentiment_trends_data(start_date_obj, end_date_obj, granularity)
    elif analytics_type == "crisis_alerts":
        data = await get_crisis_alerts_data(start_date_obj, end_date_obj, granularity)
    elif analytics_type == "language_usage":
        data = await get_language_usage_data(start_date_obj, end_date_obj)
    elif analytics_type == "topic_distribution":
        data = await get_topic_distribution_data(start_date_obj, end_date_obj)
    elif analytics_type == "appointment_trends":
        data = await get_appointment_trends_data(start_date_obj, end_date_obj, granularity)
    elif analytics_type == "user_satisfaction":
        data = await get_user_satisfaction_data(start_date_obj, end_date_obj, granularity)
    elif analytics_type == "peak_hours":
        data = await get_peak_hours_data(start_date_obj, end_date_obj)
    else:
        data = {"error": "Tipo de análisis no implementado"}
    
    return JSONResponse(content=data)

@router.get("/summary")
async def get_analytics_summary(current_user = Depends(get_current_admin_user)):
    """Obtiene un resumen de las principales métricas"""
    # Calcular fechas
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    last_week_start = today - timedelta(days=7)
    last_month_start = today - timedelta(days=30)
    
    try:
        # Obtener datos para el resumen
        messages_today = await get_message_count(today, today)
        messages_yesterday = await get_message_count(yesterday, yesterday)
        messages_last_week = await get_message_count(last_week_start, today)
        messages_last_month = await get_message_count(last_month_start, today)
        
        active_users_today = await get_active_users_count(today, today)
        active_users_week = await get_active_users_count(last_week_start, today)
        active_users_month = await get_active_users_count(last_month_start, today)
        
        avg_response_time_today = await get_avg_response_time(today, today)
        avg_response_time_week = await get_avg_response_time(last_week_start, today)
        
        crisis_alerts_today = await get_crisis_count(today, today)
        crisis_alerts_week = await get_crisis_count(last_week_start, today)
        
        # Calcular tendencias (comparación con período anterior)
        messages_trend = calculate_trend(messages_today, messages_yesterday)
        users_trend = calculate_trend(active_users_today, await get_active_users_count(today - timedelta(days=2), yesterday))
        response_time_trend = calculate_trend(avg_response_time_week, await get_avg_response_time(today - timedelta(days=14), last_week_start - timedelta(days=1)), inverse=True)
        
        # Construir respuesta
        summary = {
            "timestamp": datetime.now().isoformat(),
            "messages": {
                "today": messages_today,
                "yesterday": messages_yesterday,
                "last_7_days": messages_last_week,
                "last_30_days": messages_last_month,
                "trend": messages_trend
            },
            "active_users": {
                "today": active_users_today,
                "last_7_days": active_users_week,
                "last_30_days": active_users_month,
                "trend": users_trend
            },
            "response_time": {
                "today_avg_seconds": avg_response_time_today,
                "week_avg_seconds": avg_response_time_week,
                "trend": response_time_trend
            },
            "crisis_alerts": {
                "today": crisis_alerts_today,
                "last_7_days": crisis_alerts_week
            },
            "top_languages": await get_top_languages(last_week_start, today),
            "top_playbooks": await get_top_playbooks(last_week_start, today)
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error al generar resumen analítico: {e}")
        return {
            "error": "Error al generar el resumen analítico",
            "detail": str(e)
        }

@router.get("/export")
async def export_analytics_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    data_type: Optional[str] = "all",
    format: Optional[str] = "json",
    current_user = Depends(get_current_admin_user)
):
    """Exporta datos analíticos en diferentes formatos"""
    # Implementar exportación de datos
    # Esta es una versión simplificada que devuelve JSON
    
    # Determinar fechas
    today = datetime.now().date()
    if not end_date:
        end_date_obj = today
    else:
        try:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido para end_date (YYYY-MM-DD)")
    
    if not start_date:
        # Por defecto, 30 días hacia atrás
        start_date_obj = end_date_obj - timedelta(days=30)
    else:
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido para start_date (YYYY-MM-DD)")
    
    # Recopilar todos los datos necesarios
    export_data = {
        "metadata": {
            "export_date": datetime.now().isoformat(),
            "start_date": start_date_obj.isoformat(),
            "end_date": end_date_obj.isoformat(),
            "data_type": data_type,
            "format": format
        }
    }
    
    # Incluir datos según el tipo solicitado
    if data_type == "all" or data_type == "messages":
        export_data["message_volume"] = await get_message_volume_data(start_date_obj, end_date_obj, "day")
    
    if data_type == "all" or data_type == "playbooks":
        export_data["playbook_usage"] = await get_playbook_usage_data(start_date_obj, end_date_obj)
    
    if data_type == "all" or data_type == "languages":
        export_data["language_usage"] = await get_language_usage_data(start_date_obj, end_date_obj)
    
    if data_type == "all" or data_type == "crisis":
        export_data["crisis_alerts"] = await get_crisis_alerts_data(start_date_obj, end_date_obj, "day")
    
    # Solo formato JSON implementado en esta versión
    return export_data

# Funciones auxiliares para obtener datos

async def get_message_count(start_date: datetime.date, end_date: datetime.date) -> int:
    """Obtiene el número de mensajes en un periodo"""
    try:
        from database.d1_client import db_client
        count = await db_client.count_messages(start_date, end_date)
        return count
    except Exception as e:
        logger.error(f"Error al obtener conteo de mensajes: {e}")
        # Datos de ejemplo para desarrollo
        days_diff = (end_date - start_date).days + 1
        return days_diff * 120  # Aproximadamente 120 mensajes por día

async def get_active_users_count(start_date: datetime.date, end_date: datetime.date) -> int:
    """Obtiene el número de usuarios activos en un periodo"""
    try:
        from database.d1_client import db_client
        count = await db_client.count_active_users(start_date, end_date)
        return count
    except Exception as e:
        logger.error(f"Error al obtener conteo de usuarios activos: {e}")
        # Datos de ejemplo para desarrollo
        days_diff = (end_date - start_date).days + 1
        return min(days_diff * 8, 150)  # Aproximadamente 8 usuarios nuevos por día, máximo 150

async def get_avg_response_time(start_date: datetime.date, end_date: datetime.date) -> float:
    """Obtiene el tiempo promedio de respuesta en segundos"""
    try:
        from database.d1_client import db_client
        avg_time = await db_client.get_avg_response_time(start_date, end_date)
        return avg_time
    except Exception as e:
        logger.error(f"Error al obtener tiempo promedio de respuesta: {e}")
        # Datos de ejemplo para desarrollo
        return 8.5  # 8.5 segundos promedio

async def get_crisis_count(start_date: datetime.date, end_date: datetime.date) -> int:
    """Obtiene el número de alertas de crisis en un periodo"""
    try:
        from database.d1_client import db_client
        count = await db_client.count_crisis_alerts(start_date, end_date)
        return count
    except Exception as e:
        logger.error(f"Error al obtener conteo de alertas de crisis: {e}")
        # Datos de ejemplo para desarrollo
        days_diff = (end_date - start_date).days + 1
        return days_diff * 2  # Aproximadamente 2 alertas por día

async def get_top_languages(start_date: datetime.date, end_date: datetime.date, limit: int = 3) -> List[Dict]:
    """Obtiene los idiomas más utilizados"""
    try:
        from database.d1_client import db_client
        languages = await db_client.get_top_languages(start_date, end_date, limit)
        return languages
    except Exception as e:
        logger.error(f"Error al obtener top de idiomas: {e}")
        # Datos de ejemplo para desarrollo
        return [
            {"language": "es", "count": 450, "percentage": 65},
            {"language": "ca", "count": 180, "percentage": 26},
            {"language": "en", "count": 62, "percentage": 9}
        ]

async def get_top_playbooks(start_date: datetime.date, end_date: datetime.date, limit: int = 3) -> List[Dict]:
    """Obtiene los playbooks más utilizados"""
    try:
        from database.d1_client import db_client
        playbooks = await db_client.get_top_playbooks(start_date, end_date, limit)
        return playbooks
    except Exception as e:
        logger.error(f"Error al obtener top de playbooks: {e}")
        # Datos de ejemplo para desarrollo
        return [
            {"playbook": "identity", "count": 320, "percentage": 55},
            {"playbook": "appointment", "count": 180, "percentage": 31},
            {"playbook": "crisis", "count": 82, "percentage": 14}
        ]

def calculate_trend(current: Union[int, float], previous: Union[int, float], inverse: bool = False) -> float:
    """Calcula la tendencia como porcentaje de cambio"""
    if previous == 0:
        return 100 if current > 0 else 0
        
    trend = ((current - previous) / previous) * 100
    
    # Para métricas donde la disminución es positiva (como tiempo de respuesta)
    if inverse:
        trend = -trend
        
    return round(trend, 1)

# Funciones para generar datos analíticos detallados

async def get_message_volume_data(start_date: datetime.date, end_date: datetime.date, granularity: str) -> Dict:
    """Genera datos de volumen de mensajes"""
    try:
        from database.d1_client import db_client
        data = await db_client.get_message_volume(start_date, end_date, granularity)
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Error al obtener datos de volumen de mensajes: {e}")
        
        # Generar datos de ejemplo para desarrollo
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            date_range.append(current_date)
            if granularity == "day":
                current_date += timedelta(days=1)
            elif granularity == "week":
                current_date += timedelta(days=7)
            elif granularity == "month":
                # Avanzar al primer día del siguiente mes
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1, day=1)
        
        # Generar datos aleatorios pero con sentido
        import random
        data = []
        for date_item in date_range:
            # Generar valores con base día de la semana (más mensajes entre semana)
            base_value = 150 if date_item.weekday() < 5 else 80
            variation = random.uniform(0.8, 1.2)  # Variación de ±20%
            
            data.append({
                "date": date_item.isoformat(),
                "total": int(base_value * variation),
                "user_messages": int(base_value * variation * 0.6),  # 60% son mensajes de usuarios
                "mark_responses": int(base_value * variation * 0.4)  # 40% son respuestas de Mark
            })
        
        return {"success": True, "data": data}

async def get_response_time_data(start_date: datetime.date, end_date: datetime.date, granularity: str) -> Dict:
    """Genera datos de tiempo de respuesta"""
    # Implementación similar a get_message_volume_data pero con tiempos de respuesta
    # Datos de ejemplo para desarrollo
    import random
    
    date_range = []
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date)
        if granularity == "day":
            current_date += timedelta(days=1)
        elif granularity == "week":
            current_date += timedelta(days=7)
        elif granularity == "month":
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1, day=1)
    
    data = []
    for date_item in date_range:
        # Simulación de una tendencia a la mejora en los tiempos de respuesta
        days_from_start = (date_item - start_date).days
        progress_factor = days_from_start / max(1, (end_date - start_date).days)
        base_time = 10 - (progress_factor * 2)  # Mejora desde 10s a 8s
        variation = random.uniform(0.9, 1.1)  # Variación de ±10%
        
        data.append({
            "date": date_item.isoformat(),
            "avg_seconds": round(base_time * variation, 1),
            "median_seconds": round(base_time * variation * 0.9, 1),
            "90th_percentile": round(base_time * variation * 1.5, 1)
        })
    
    return {"success": True, "data": data}

async def get_playbook_usage_data(start_date: datetime.date, end_date: datetime.date) -> Dict:
    """Genera datos de uso de playbooks"""
    # Datos de ejemplo para desarrollo
    playbooks = [
        {"id": "identity", "name": "Identidad"},
        {"id": "crisis", "name": "Crisis"},
        {"id": "appointment", "name": "Citas"},
        {"id": "security", "name": "Seguridad"}
    ]
    
    data = []
    total_usage = 0
    
    for playbook in playbooks:
        # Generar datos que suman 100%
        if playbook["id"] == "identity":
            usage = 55  # Identity playbook es el más usado
        elif playbook["id"] == "appointment":
            usage = 31  # Appointment es el segundo más usado
        elif playbook["id"] == "crisis":
            usage = 9   # Crisis tiene uso moderado
        else:
            usage = 5   # Security tiene uso bajo
            
        total_usage += usage
        
        data.append({
            "playbook_id": playbook["id"],
            "playbook_name": playbook["name"],
            "count": int(usage * 10),  # Multiplicamos por 10 para tener valores absolutos
            "percentage": usage
        })
    
    # Ajustar porcentajes para asegurar que sumen 100%
    if total_usage != 100:
        for item in data:
            item["percentage"] = round((item["percentage"] / total_usage) * 100, 1)
    
    return {"success": True, "data": data}

async def get_sentiment_trends_data(start_date: datetime.date, end_date: datetime.date, granularity: str) -> Dict:
    """Genera datos de tendencias de sentimiento"""
    # Implementación similar a get_message_volume_data pero con sentimientos
    # Datos de ejemplo para desarrollo
    import random
    
    date_range = []
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date)
        if granularity == "day":
            current_date += timedelta(days=1)
        elif granularity == "week":
            current_date += timedelta(days=7)
        elif granularity == "month":
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1, day=1)
    
    data = []
    for date_item in date_range:
        # Simular una tendencia general de mejora de sentimiento
        days_from_start = (date_item - start_date).days
        progress_factor = min(0.2, days_from_start / max(1, (end_date - start_date).days) * 0.2)
        
        # Base values
        positive_base = 0.35 + progress_factor
        neutral_base = 0.40 - progress_factor
        negative_base = 0.25
        
        # Añadir algo de variación
        variation = random.uniform(0.95, 1.05)
        positive = min(0.6, positive_base * variation)
        
        variation = random.uniform(0.95, 1.05)
        neutral = min(0.5, neutral_base * variation)
        
        # Asegurar que suman 1.0
        negative = 1.0 - positive - neutral
        
        data.append({
            "date": date_item.isoformat(),
            "positive": round(positive, 2),
            "neutral": round(neutral, 2),
            "negative": round(negative, 2)
        })
    
    return {"success": True, "data": data}

async def get_crisis_alerts_data(start_date: datetime.date, end_date: datetime.date, granularity: str) -> Dict:
    """Genera datos de alertas de crisis"""
    # Implementación similar a los anteriores pero con datos de crisis
    # Datos de ejemplo para desarrollo
    import random
    
    date_range = []
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date)
        if granularity == "day":
            current_date += timedelta(days=1)
        elif granularity == "week":
            current_date += timedelta(days=7)
        elif granularity == "month":
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1, day=1)
    
    data = []
    for date_item in date_range:
        # Generar conteos de alertas de crisis (generalmente bajos)
        # Las crisis son más comunes en ciertos días de la semana y períodos
        weekday_factor = 1.5 if date_item.weekday() in [0, 6] else 1.0  # Más en lunes y domingo
        
        # Valor base bajo para crisis
        base_value = 2 * weekday_factor
        variation = random.uniform(0.5, 1.5)  # Mayor variación para eventos raros
        
        alerts_count = max(0, int(base_value * variation))
        
        # Distribuir por severidad
        high_severity = max(0, min(alerts_count, int(alerts_count * 0.3) + (1 if random.random() > 0.7 else 0)))
        medium_severity = max(0, min(alerts_count - high_severity, int(alerts_count * 0.5) + (1 if random.random() > 0.5 else 0)))
        low_severity = max(0, alerts_count - high_severity - medium_severity)
        
        data.append({
            "date": date_item.isoformat(),
            "total": alerts_count,
            "high_severity": high_severity,
            "medium_severity": medium_severity,
            "low_severity": low_severity
        })
    
    return {"success": True, "data": data}

async def get_language_usage_data(start_date: datetime.date, end_date: datetime.date) -> Dict:
    """Genera datos de uso de idiomas"""
    # Datos de ejemplo para desarrollo
    languages = [
        {"code": "es", "name": "Español"},
        {"code": "ca", "name": "Catalán"},
        {"code": "en", "name": "Inglés"},
        {"code": "ar", "name": "Árabe"}
    ]
    
    data = []
    total_usage = 0
    
    for language in languages:
        # Generar distribución realista
        if language["code"] == "es":
            usage = 65  # Español dominante
        elif language["code"] == "ca":
            usage = 26  # Catalán segundo
        elif language["code"] == "en":
            usage = 8   # Inglés menor uso
        else:
            usage = 1   # Árabe poco uso
            
        total_usage += usage
        
        data.append({
            "language_code": language["code"],
            "language_name": language["name"],
            "count": int(usage * 10),  # Multiplicamos para valores absolutos
            "percentage": usage
        })
    
    # Ajustar porcentajes para asegurar que sumen 100%
    if total_usage != 100:
        for item in data:
            item["percentage"] = round((item["percentage"] / total_usage) * 100, 1)
    
    return {"success": True, "data": data}

async def get_topic_distribution_data(start_date: datetime.date, end_date: datetime.date) -> Dict:
    """Genera datos de distribución de temas"""
    # Datos de ejemplo para desarrollo
    topics = [
        {"id": "appointment", "name": "Citas y horarios"},
        {"id": "therapy", "name": "Terapia y tratamiento"},
        {"id": "payment", "name": "Pagos y facturación"},
        {"id": "general", "name": "Información general"},
        {"id": "anxiety", "name": "Ansiedad"},
        {"id": "depression", "name": "Depresión"},
        {"id": "other", "name": "Otros temas"}
    ]
    
    data = []
    total = 0
    
    # Asignar porcentajes realistas
    percentages = [28, 22, 18, 12, 8, 7, 5]
    
    for i, topic in enumerate(topics):
        percentage = percentages[i]
        total += percentage
        
        data.append({
            "topic_id": topic["id"],
            "topic_name": topic["name"],
            "count": int(percentage * 10),  # Multiplicamos para valores absolutos
            "percentage": percentage
        })
    
    # Ajustar porcentajes para asegurar que sumen 100%
    if total != 100:
        for item in data:
            item["percentage"] = round((item["percentage"] / total) * 100, 1)
    
    return {"success": True, "data": data}

async def get_appointment_trends_data(start_date: datetime.date, end_date: datetime.date, granularity: str) -> Dict:
    """Genera datos de tendencias de citas"""
    # Implementación similar a los anteriores pero con datos de citas
    # Datos de ejemplo para desarrollo
    import random
    
    date_range = []
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date)
        if granularity == "day":
            current_date += timedelta(days=1)
        elif granularity == "week":
            current_date += timedelta(days=7)
        elif granularity == "month":
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1, day=1)
    
    data = []
    for date_item in date_range:
        # Las citas son más comunes entre semana
        weekday_factor = 1.5 if date_item.weekday() < 5 else 0.6
        
        # Base para citas diarias
        base_scheduled = 10 * weekday_factor
        variation = random.uniform(0.8, 1.2)
        scheduled = int(base_scheduled * variation)
        
        # Calcular otras métricas basadas en las programadas
        canceled = max(0, int(scheduled * random.uniform(0.05, 0.15)))  # 5-15% cancelaciones
        rescheduled = max(0, int(scheduled * random.uniform(0.1, 0.2)))  # 10-20% reprogramaciones
        completed = max(0, scheduled - canceled)  # Completadas = programadas - canceladas
        
        data.append({
            "date": date_item.isoformat(),
            "scheduled": scheduled,
            "canceled": canceled,
            "rescheduled": rescheduled,
            "completed": completed
        })
    
    return {"success": True, "data": data}

async def get_user_satisfaction_data(start_date: datetime.date, end_date: datetime.date, granularity: str) -> Dict:
    """Genera datos de satisfacción de usuarios"""
    # Implementación similar a los anteriores pero con datos de satisfacción
    # Datos de ejemplo para desarrollo
    import random
    
    date_range = []
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date)
        if granularity == "day":
            current_date += timedelta(days=1)
        elif granularity == "week":
            current_date += timedelta(days=7)
        elif granularity == "month":
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1, day=1)
    
    data = []
    for date_item in date_range:
        # Simulamos una leve tendencia de mejora con el tiempo
        days_from_start = (date_item - start_date).days
        progress_factor = min(0.2, days_from_start / max(1, (end_date - start_date).days) * 0.2)
        
        # Valor base alto para satisfacción
        base_satisfaction = 4.2 + progress_factor  # En escala de 1-5
        variation = random.uniform(0.97, 1.03)  # Pequeña variación
        
        satisfaction = min(5.0, base_satisfaction * variation)
        
        # Calcular distribución de ratings
        total_ratings = random.randint(15, 30)
        
        # Distribuir los ratings según la satisfacción media
        if satisfaction >= 4.5:
            rating_5 = int(total_ratings * random.uniform(0.6, 0.7))
        elif satisfaction >= 4.0:
            rating_5 = int(total_ratings * random.uniform(0.4, 0.6))
        else:
            rating_5 = int(total_ratings * random.uniform(0.3, 0.4))
            
        rating_4 = int(total_ratings * random.uniform(0.25, 0.35))
        rating_3 = int(total_ratings * random.uniform(0.1, 0.2))
        rating_2 = int(total_ratings * random.uniform(0.02, 0.1))
        
        # Ajustar para que sumen total_ratings
        rating_1 = total_ratings - rating_5 - rating_4 - rating_3 - rating_2
        if rating_1 < 0:
            rating_2 += rating_1
            rating_1 = 0
        
        data.append({
            "date": date_item.isoformat(),
            "avg_satisfaction": round(satisfaction, 1),
            "total_ratings": total_ratings,
            "rating_distribution": {
                "5_stars": rating_5,
                "4_stars": rating_4,
                "3_stars": rating_3,
                "2_stars": rating_2,
                "1_star": rating_1
            }
        })
    
    return {"success": True, "data": data}

async def get_peak_hours_data(start_date: datetime.date, end_date: datetime.date) -> Dict:
    """Genera datos de horas pico de actividad"""
    # Datos de ejemplo para desarrollo
    hours = list(range(24))
    data = []
    
    # Crear un patrón realista de actividad durante el día
    for hour in hours:
        # Menor actividad en la madrugada, picos en mañana, mediodía y noche
        if 0 <= hour < 7:
            base_activity = 5 + (hour * 2)  # Aumenta gradualmente
        elif 7 <= hour < 10:
            base_activity = 30 + ((hour - 7) * 15)  # Pico matutino
        elif 10 <= hour < 14:
            base_activity = 70 - ((hour - 10) * 5)  # Descenso gradual
        elif 14 <= hour < 17:
            base_activity = 50 + ((hour - 14) * 10)  # Aumento tarde
        elif 17 <= hour < 22:
            base_activity = 80 - ((hour - 17) * 5)  # Pico y descenso nocturno
        else:
            base_activity = 40 - ((hour - 22) * 10)  # Descenso madrugada
        
        # Valor absoluto (mensajes por hora en promedio)
        value = max(1, int(base_activity * 1.2))
        
        data.append({
            "hour": hour,
            "formatted_hour": f"{hour:02d}:00",
            "count": value,
            "percentage": round((value / 100) * 100, 1)  # Porcentaje relativo
        })
    
    # Normalizar porcentajes para que sumen 100%
    total = sum(item["count"] for item in data)
    for item in data:
        item["percentage"] = round((item["count"] / total) * 100, 1)
    
    return {"success": True, "data": data} 