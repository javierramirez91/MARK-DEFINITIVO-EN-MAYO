"""
Mensajes en español para el asistente Mark.
Este es el idioma por defecto del sistema.
"""

messages = {
    "welcome": {
        "greeting": "¡Hola! Soy Mark, el asistente del Centre de Psicologia Jaume I. ¿En qué puedo ayudarte hoy? 😊",
        "returning": "¡Bienvenido de nuevo! ¿En qué puedo ayudarte hoy? 😊"
    },
    
    "intake": {
        "welcome": "Hola, soy {assistant_name}, el asistente del Centre de Psicologia Jaume I. Voy a ayudarte con el proceso inicial para comenzar terapia. 😊",
        "collect_personal": "Para comenzar, necesito algunos datos para conocer mejor tus necesidades y ofrecerte una atención personalizada y confidencial. 📋 Por favor, facilítame esta información:\n\n1️⃣ Nombre y apellidos\n2️⃣ Teléfono\n3️⃣ Correo electrónico\n4️⃣ Disponibilidad: Mañanas / Tardes / Indiferente\n5️⃣ Idioma de preferencia: Catalán, Castellano, Inglés, Árabe\n6️⃣ Motivo de consulta: ¿Qué te gustaría trabajar o mejorar en terapia?\n7️⃣ Motivación: ¿Qué esperas obtener de la terapia? ¿En qué crees que puede ayudarte la terapia?\n8️⃣ Dudas o preocupaciones respecto al inicio de la terapia?",
        "missing_fields": "Aún necesito un poco más de información. Por favor, proporciona los siguientes datos: {fields}",
        "personal_info_confirmation": "¡Perfecto! He registrado tus datos:\n\n- Nombre: {name}\n- Teléfono: {phone}\n- Email: {email}\n- Motivo de consulta: {reason}\n\nAhora vamos a identificar qué tipo de terapia podría ser más adecuada para ti.",
        "specialty_identified": "Según tu motivo de consulta, creo que la especialidad en {specialty} podría ser la más adecuada para ti.",
        "no_specialist": "En este momento no tenemos un especialista disponible en {specialty}, pero contamos con terapeutas con experiencia en diversas áreas que pueden ayudarte.",
        "session_format": "¿Prefieres que las sesiones sean presenciales en nuestra consulta o en formato online?",
        "clarify_format": "No me ha quedado claro tu preferencia. ¿Podrías indicarme si prefieres las sesiones online (por videollamada) o presenciales (en nuestra consulta)?",
        "format_confirmation": "¡Entendido! Has elegido formato {format} para tus sesiones.",
        "scheduling_info": "A continuación, vamos a programar una primera llamada gratuita para resolver cualquier duda que tengas y buscar al terapeuta que mejor se adapte a tus necesidades.",
        "completion": "Gracias por proporcionar toda esta información. En breve me pondré en contacto contigo para confirmar la fecha y hora de tu primera llamada gratuita. Si tienes cualquier duda mientras tanto, no dudes en preguntarme. 😊"
    },
    
    "scheduling": {
        "available_slots": "Estos son los horarios disponibles para tu primera cita:\n\n{slots}\n\nPor favor, indícame qué opción prefieres.",
        "confirmation": "¡Cita confirmada! Te esperamos el {date} a las {time}. Recibirás un recordatorio 48 horas antes.",
        "reminder": "Te recuerdo que tienes una cita programada para mañana {date} a las {time}. ¿Podrás asistir?",
        "cancellation_policy": "Recuerda que las cancelaciones con menos de 24 horas de antelación tienen un cargo de 30€.",
        "reschedule_options": "Entiendo que necesitas cambiar tu cita. Estas son las opciones disponibles:\n\n{options}\n\n¿Cuál prefieres?"
    },
    
    "payments": {
        "payment_link": "Para completar la reserva de tu cita, puedes realizar el pago aquí: {link} ✅",
        "payment_confirmation": "¡Pago recibido! Tu cita está confirmada.",
        "payment_reminder": "Te recuerdo que aún está pendiente el pago de tu sesión. Puedes realizarlo aquí: {link}",
        "receipt": "Adjunto encontrarás el recibo de tu pago. ¡Gracias!"
    },
    
    "crisis": {
        "initial_response": "Lamento mucho que estés pasando por esto. Recuerda que no estás solo/a. Estamos aquí para ayudarte. ¿Necesitas hablar con tu profesional de confianza?",
        "emergency_notification": "De acuerdo, ya hemos notificado a {emergency_contact} y su equipo. Se pondrán en contacto contigo lo antes posible.",
        "resources": "Mientras tanto, aquí tienes algunas herramientas que pueden ayudarte:\n\n1️⃣ Respiración profunda: Inhala durante 4 segundos, mantén 4 segundos, exhala 4 segundos.\n2️⃣ Mindfulness: Observa 5 cosas que puedas ver, 4 que puedas tocar, 3 que puedas oír, 2 que puedas oler y 1 que puedas saborear.\n3️⃣ Contacta con alguien de confianza para hablar.",
        "emergency_services": "Si necesitas ayuda inmediata, puedes contactar con los servicios de emergencia al 112 o con el 024 (Servicio de Atención a la Conducta Suicida)."
    },
    
    "followup": {
        "post_session": "¿Cómo te has sentido después de la sesión de hoy? Me gustaría saber si hay algo que quieras compartir o alguna duda que te haya surgido.",
        "feedback_request": "Nos gustaría conocer tu opinión sobre tu experiencia hasta ahora. ¿Podrías valorar del 1 al 10 cómo te estás sintiendo con la terapia?",
        "resources_offer": "Tu terapeuta ha recomendado algunos recursos que podrían serte útiles. ¿Te gustaría recibirlos?"
    },
    
    "errors": {
        "general": "Lo siento, ha ocurrido un error. Por favor, inténtalo de nuevo más tarde.",
        "processing_info": "Lo siento, ha habido un problema al procesar tu información. ¿Podrías intentarlo de nuevo?",
        "processing_specialty": "Ha habido un problema al determinar la especialidad adecuada, pero no te preocupes, seguiremos con el proceso.",
        "saving_patient": "Ha habido un problema al guardar tus datos, pero no te preocupes, seguiremos con el proceso. Por favor, mantén una copia de la información que me has proporcionado.",
        "scheduling": "Lo siento, ha habido un problema al programar la cita. Por favor, inténtalo de nuevo o contáctanos por teléfono."
    },
    
    "security": {
        "unauthorized": "Lo siento, solo puedo aceptar órdenes de modificación del número autorizado. Si eres {admin_name}, envíame un mensaje desde tu número personal ({admin_phone}).",
        "confidentiality": "Lo siento, no puedo proporcionar información sobre otros pacientes por razones de confidencialidad."
    },
    
    "fields": {
        "name": "nombre y apellidos",
        "phone": "teléfono",
        "email": "correo electrónico",
        "availability": "disponibilidad",
        "language_preference": "idioma preferido",
        "consultation_reason": "motivo de consulta",
        "expectations": "expectativas de la terapia",
        "concerns": "dudas o preocupaciones"
    },
    
    "specialties": {
        "ansiedad": "ansiedad",
        "depresion": "depresión",
        "trauma": "trauma",
        "pareja": "terapia de pareja o familiar",
        "adicciones": "adicciones",
        "infantil": "psicología infantil",
        "adolescentes": "psicología de adolescentes",
        "general": "psicología general"
    },
    
    "formats": {
        "online": "online (videollamada)",
        "presencial": "presencial (en consulta)"
    },
    
    "confirmation": {
        "yes": "sí",
        "no": "no",
        "maybe": "quizás"
    },
    
    "fallback": {
        "not_understood": "Lo siento, no he entendido tu mensaje. ¿Podrías reformularlo?",
        "need_more_info": "Necesito un poco más de información para poder ayudarte correctamente.",
        "suggest_options": "Puedo ayudarte con:\n\n- Programar o modificar citas\n- Información sobre tarifas y servicios\n- Resolver dudas sobre la terapia\n- Contactar con tu terapeuta\n\n¿En qué te puedo ayudar?"
    }
}

# Alias para compatibilidad
MESSAGES = messages 