"""
Sistema de detección de amenazas para el asistente Mark.
Identifica situaciones donde un paciente podría representar un peligro para sí mismo o para otros.
"""
import logging
import json
import re
from typing import Dict, List, Optional, Any, Set, Tuple

# Configurar logging
logger = logging.getLogger("mark.threat-detection")

class ThreatDetector:
    """
    Detector de amenazas para identificar situaciones de riesgo.
    Analiza mensajes para detectar indicios de autolesión, suicidio, daño a terceros, etc.
    """
    
    def __init__(self):
        """Inicializar el detector de amenazas"""
        # Palabras clave de alto riesgo (multilingüe)
        self.high_risk_keywords = {
            # Español
            "es": [
                "suicidio", "suicidarme", "quitarme la vida", "acabar con todo", "matarme",
                "cortarme", "no quiero vivir más", "sobredosis", "pastillas", "saltar",
                "ahorcarme", "colgarme", "despedirme", "última oportunidad", "última voluntad",
                "nadie me echará de menos", "mejor sin mí", "no puedo más",
                "amenaza", "matar", "asesinar", "arma", "pistola", "cuchillo", "bomba",
                "venganza", "vengarse", "hacer daño", "disparar", "atacar"
            ],
            # Catalán
            "ca": [
                "suïcidi", "suïcidar-me", "treure'm la vida", "acabar amb tot", "matar-me",
                "tallar-me", "no vull viure més", "sobredosi", "pastilles", "saltar",
                "penjar-me", "acomiadar-me", "última oportunitat", "última voluntat",
                "ningú em trobarà a faltar", "millor sense mi", "no puc més",
                "amenaça", "matar", "assassinar", "arma", "pistola", "ganivet", "bomba",
                "venjança", "venjar-se", "fer mal", "disparar", "atacar"
            ],
            # Inglés
            "en": [
                "suicide", "kill myself", "end my life", "end it all", "take my life",
                "cutting myself", "don't want to live", "overdose", "pills", "jump",
                "hang myself", "goodbye letter", "last chance", "last will",
                "nobody will miss me", "better off without me", "can't take it anymore",
                "threat", "kill", "murder", "weapon", "gun", "knife", "bomb",
                "revenge", "get revenge", "hurt", "shoot", "attack"
            ],
            # Árabe (transliteración)
            "ar": [
                "انتحار", "اقتل نفسي", "انهاء حياتي", "انهاء كل شيء", "اخذ حياتي",
                "اقطع نفسي", "لا اريد العيش", "جرعة زائدة", "حبوب", "اقفز",
                "اشنق نفسي", "رسالة وداع", "آخر فرصة", "الوصية الاخيرة",
                "لن يفتقدني أحد", "أفضل بدوني", "لا استطيع تحمل المزيد",
                "تهديد", "قتل", "قاتل", "سلاح", "مسدس", "سكين", "قنبلة",
                "انتقام", "ينتقم", "يؤذي", "اطلاق النار", "هجوم"
            ]
        }
        
        # Indicadores contextuales de riesgo (multilingüe)
        self.contextual_indicators = {
            # Español
            "es": [
                "he preparado todo", "escribí una nota", "regalé mis cosas", 
                "ya lo tengo todo planeado", "hoy es el día", "ya no estaré aquí",
                "todo está listo", "he tomado mi decisión", "no hay marcha atrás",
                "no tengo otra opción", "no veo otra salida", "ya no aguanto más",
                "lo voy a hacer", "cuando amanezca", "esta noche", "en unas horas"
            ],
            # Catalán
            "ca": [
                "ho tinc tot preparat", "he escrit una nota", "he regalat les meves coses",
                "ja ho tinc tot planejat", "avui és el dia", "ja no seré aquí",
                "tot està a punt", "he pres la meva decisió", "no hi ha marxa enrere",
                "no tinc altra opció", "no veig altra sortida", "ja no aguanto més",
                "ho faré", "quan surti el sol", "aquesta nit", "en unes hores"
            ],
            # Inglés
            "en": [
                "i have prepared everything", "wrote a note", "gave away my things",
                "it's all planned", "today is the day", "i won't be here anymore",
                "everything is ready", "i've made my decision", "no turning back",
                "i have no other choice", "i see no way out", "i can't take it anymore",
                "i'm going to do it", "when dawn breaks", "tonight", "in a few hours"
            ],
            # Árabe (transliteración)
            "ar": [
                "لقد أعددت كل شيء", "كتبت ملاحظة", "أعطيت أشيائي",
                "كل شيء مخطط له", "اليوم هو اليوم", "لن أكون هنا بعد الآن",
                "كل شيء جاهز", "لقد اتخذت قراري", "لا عودة",
                "ليس لدي خيار آخر", "لا أرى مخرجا", "لا أستطيع تحمل المزيد",
                "سأفعل ذلك", "عند الفجر", "الليلة", "خلال ساعات قليلة"
            ]
        }
        
        # Patrones temporales que indican inmediatez
        self.temporal_indicators = {
            # Español
            "es": [
                r"(hoy|esta noche|ahora|en\s+\d+\s+minutos|en\s+\d+\s+horas|mañana|luego|después)",
                r"(ya no aguanto más|no puedo seguir así|esto acaba hoy)"
            ],
            # Catalán
            "ca": [
                r"(avui|aquesta nit|ara|en\s+\d+\s+minuts|en\s+\d+\s+hores|demà|després|més tard)",
                r"(ja no aguanto més|no puc seguir així|això s'acaba avui)"
            ],
            # Inglés
            "en": [
                r"(today|tonight|now|in\s+\d+\s+minutes|in\s+\d+\s+hours|tomorrow|later|after)",
                r"(can't take it anymore|can't go on like this|this ends today)"
            ],
            # Árabe (simplificado para código)
            "ar": [
                r"(اليوم|الليلة|الآن|بعد|غدا|لاحقا)",
                r"(لا أستطيع تحمل المزيد|لا يمكنني الاستمرار|هذا ينتهي اليوم)"
            ]
        }
        
        # Inicializar modelo de análisis de severidad (mock)
        self.severity_model_ready = False
        try:
            # En un sistema real, aquí cargaríamos un modelo para evaluar la severidad
            # from transformers import pipeline
            # self.severity_model = pipeline("text-classification", model="model_name")
            self.severity_model_ready = False  # Cambiar a True cuando se implemente
        except:
            logger.error("No se pudo cargar el modelo de evaluación de severidad")
    
    def _contains_high_risk_keywords(self, text: str, language: str) -> List[str]:
        """
        Verifica si el texto contiene palabras clave de alto riesgo.
        
        Args:
            text: Texto a analizar
            language: Código de idioma
            
        Returns:
            Lista de palabras clave encontradas
        """
        # Normalizar texto
        text = text.lower()
        
        # Si no tenemos el idioma específico, usar español por defecto
        if language not in self.high_risk_keywords:
            language = "es"
            
        # Buscar palabras clave
        found_keywords = []
        for keyword in self.high_risk_keywords[language]:
            if keyword in text:
                found_keywords.append(keyword)
                
        return found_keywords
    
    def _contains_contextual_indicators(self, text: str, language: str) -> List[str]:
        """
        Verifica si el texto contiene indicadores contextuales de riesgo.
        
        Args:
            text: Texto a analizar
            language: Código de idioma
            
        Returns:
            Lista de indicadores contextuales encontrados
        """
        # Normalizar texto
        text = text.lower()
        
        # Si no tenemos el idioma específico, usar español por defecto
        if language not in self.contextual_indicators:
            language = "es"
            
        # Buscar indicadores contextuales
        found_indicators = []
        for indicator in self.contextual_indicators[language]:
            if indicator in text:
                found_indicators.append(indicator)
                
        return found_indicators
    
    def _contains_temporal_indicators(self, text: str, language: str) -> bool:
        """
        Verifica si el texto contiene indicadores temporales que sugieren inmediatez.
        
        Args:
            text: Texto a analizar
            language: Código de idioma
            
        Returns:
            True si se encuentran indicadores temporales, False en caso contrario
        """
        # Normalizar texto
        text = text.lower()
        
        # Si no tenemos el idioma específico, usar español por defecto
        if language not in self.temporal_indicators:
            language = "es"
            
        # Buscar patrones temporales
        for pattern in self.temporal_indicators[language]:
            if re.search(pattern, text):
                return True
                
        return False
    
    async def evaluate_severity_with_claude(self, text: str) -> Dict[str, Any]:
        """
        Evalúa la severidad del riesgo utilizando Claude.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Diccionario con evaluación de riesgo
        """
        try:
            from ai.claude.client import generate_claude_response
            
            prompt = f"""
            Evalúa el siguiente mensaje para determinar el nivel de riesgo de daño a sí mismo o a otros.
            
            Mensaje: "{text}"
            
            Analiza:
            1. Riesgo de autolesión o suicidio
            2. Riesgo de daño a terceros
            3. Urgencia (inmediata, en horas, días, indeterminada)
            4. Presencia de un plan concreto
            5. Acceso a medios para causar daño
            
            Responde en formato JSON estrictamente con esta estructura:
            {{
                "riesgo_autolesion": "alto"|"medio"|"bajo"|"ninguno",
                "riesgo_daño_terceros": "alto"|"medio"|"bajo"|"ninguno",
                "urgencia": "inmediata"|"horas"|"días"|"indeterminada",
                "plan_concreto": true|false,
                "acceso_medios": true|false|"desconocido",
                "nivel_alerta": "crítico"|"alto"|"medio"|"bajo",
                "notificar_autoridades": true|false
            }}
            """
            
            response = await generate_claude_response(prompt, max_tokens=500, temperature=0.1)
            
            try:
                # Intentar parsear el JSON
                return json.loads(response)
            except:
                logger.error(f"No se pudo parsear la respuesta como JSON: {response}")
                return {
                    "riesgo_autolesion": "desconocido",
                    "riesgo_daño_terceros": "desconocido",
                    "urgencia": "indeterminada",
                    "plan_concreto": False,
                    "acceso_medios": "desconocido",
                    "nivel_alerta": "medio",  # Por precaución
                    "notificar_autoridades": False
                }
                
        except Exception as e:
            logger.error(f"Error al evaluar severidad con Claude: {e}")
            return {
                "riesgo_autolesion": "desconocido",
                "riesgo_daño_terceros": "desconocido",
                "urgencia": "indeterminada",
                "plan_concreto": False,
                "acceso_medios": "desconocido",
                "nivel_alerta": "medio",  # Por precaución
                "notificar_autoridades": False
            }
    
    async def analyze_message(self, message: str, language: str = "es") -> Dict[str, Any]:
        """
        Analiza un mensaje para detectar posibles amenazas o situaciones de riesgo.
        
        Args:
            message: Mensaje a analizar
            language: Código de idioma
            
        Returns:
            Diccionario con resultados del análisis
        """
        # Buscar palabras clave de alto riesgo
        high_risk_keywords = self._contains_high_risk_keywords(message, language)
        
        # Buscar indicadores contextuales
        contextual_indicators = self._contains_contextual_indicators(message, language)
        
        # Buscar indicadores temporales
        temporal_urgency = self._contains_temporal_indicators(message, language)
        
        # Determinar nivel de riesgo preliminar
        risk_level = "bajo"
        if high_risk_keywords:
            risk_level = "medio"
            if len(high_risk_keywords) >= 2 or (high_risk_keywords and contextual_indicators):
                risk_level = "alto"
                if temporal_urgency:
                    risk_level = "crítico"
        
        # Si hay riesgo medio o superior, hacer análisis detallado
        detailed_assessment = {}
        if risk_level in ["medio", "alto", "crítico"]:
            detailed_assessment = await self.evaluate_severity_with_claude(message)
        
        # Construir resultado
        result = {
            "risk_level": risk_level,
            "high_risk_keywords": high_risk_keywords,
            "contextual_indicators": contextual_indicators,
            "temporal_urgency": temporal_urgency,
            "requires_notification": risk_level in ["alto", "crítico"],
            "requires_immediate_action": risk_level == "crítico",
            "detailed_assessment": detailed_assessment
        }
        
        # Logging de eventos de alto riesgo
        if risk_level in ["alto", "crítico"]:
            logger.warning(f"Mensaje de alto riesgo detectado: {result}")
        
        return result
    
    async def determine_response_strategy(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determina la estrategia de respuesta basada en el análisis de riesgo.
        
        Args:
            analysis_result: Resultado del análisis de riesgo
            
        Returns:
            Estrategia de respuesta
        """
        risk_level = analysis_result.get("risk_level", "bajo")
        detailed = analysis_result.get("detailed_assessment", {})
        
        # Determinar si se debe notificar a las autoridades o profesionales
        notify_authorities = False
        notify_therapist = False
        
        if risk_level == "crítico":
            notify_authorities = True
            notify_therapist = True
        elif risk_level == "alto":
            notify_therapist = True
            # Notificar autoridades si hay riesgo inminente de daño a terceros
            if detailed.get("riesgo_daño_terceros") == "alto" and detailed.get("urgencia") == "inmediata":
                notify_authorities = True
        
        # Construir estrategia de respuesta
        response_strategy = {
            "approach": "support" if risk_level in ["bajo", "medio"] else "crisis_intervention",
            "tone": "calm_supportive",
            "provide_resources": True,
            "notify_therapist": notify_therapist,
            "notify_authorities": notify_authorities,
            "emergency_contacts": notify_therapist or risk_level in ["alto", "crítico"],
            "follow_up_required": risk_level != "bajo",
            "response_priority": "high" if risk_level in ["alto", "crítico"] else "normal"
        }
        
        return response_strategy


# Crear instancia del detector para exportar
threat_detector = ThreatDetector() 