"""
English messages for the Mark assistant.
"""

messages = {
    "welcome": {
        "greeting": "Hello! I'm Mark, the assistant at the Jaume I Psychology Center. How can I help you today? 😊",
        "returning": "Welcome back! How can I help you today? 😊"
    },
    
    "intake": {
        "welcome": "Hello, I'm {assistant_name}, the assistant at the Jaume I Psychology Center. I'll help you with the initial process to start therapy. 😊",
        "collect_personal": "To begin, I need some information to better understand your needs and offer you personalized and confidential care. 📋 Please provide me with this information:\n\n1️⃣ Full name\n2️⃣ Phone number\n3️⃣ Email address\n4️⃣ Availability: Mornings / Afternoons / No preference\n5️⃣ Preferred language: Catalan, Spanish, English, Arabic\n6️⃣ Reason for consultation: What would you like to work on or improve in therapy?\n7️⃣ Motivation: What do you expect to get from therapy? How do you think therapy can help you?\n8️⃣ Any doubts or concerns about starting therapy?",
        "missing_fields": "I still need a bit more information. Please provide the following details: {fields}",
        "personal_info_confirmation": "Perfect! I've registered your information:\n\n- Name: {name}\n- Phone: {phone}\n- Email: {email}\n- Reason for consultation: {reason}\n\nNow we'll identify what type of therapy might be most suitable for you.",
        "specialty_identified": "Based on your reason for consultation, I believe that the specialty in {specialty} might be the most appropriate for you.",
        "no_specialist": "At this time we don't have a specialist available in {specialty}, but we have therapists with experience in various areas who can help you.",
        "session_format": "Do you prefer in-person sessions at our office or online format?",
        "clarify_format": "I'm not clear about your preference. Could you indicate if you prefer online sessions (via video call) or in-person sessions (at our office)?",
        "format_confirmation": "Understood! You've chosen {format} format for your sessions.",
        "scheduling_info": "Next, we'll schedule a free initial call to address any questions you might have and find the therapist who best suits your needs.",
        "completion": "Thank you for providing all this information. I'll contact you shortly to confirm the date and time of your free initial call. If you have any questions in the meantime, don't hesitate to ask me. 😊"
    },
    
    "scheduling": {
        "available_slots": "These are the available times for your first appointment:\n\n{slots}\n\nPlease let me know which option you prefer.",
        "confirmation": "Appointment confirmed! We'll see you on {date} at {time}. You'll receive a reminder 48 hours before.",
        "reminder": "I'd like to remind you that you have an appointment scheduled for tomorrow {date} at {time}. Will you be able to attend?",
        "cancellation_policy": "Please remember that cancellations with less than 24 hours notice incur a €30 charge.",
        "reschedule_options": "I understand you need to change your appointment. These are the available options:\n\n{options}\n\nWhich do you prefer?"
    },
    
    "payments": {
        "payment_link": "To complete your appointment reservation, you can make the payment here: {link} ✅",
        "payment_confirmation": "Payment received! Your appointment is confirmed.",
        "payment_reminder": "I'd like to remind you that the payment for your session is still pending. You can make it here: {link}",
        "receipt": "Attached you'll find the receipt for your payment. Thank you!"
    },
    
    "crisis": {
        "initial_response": "I'm very sorry you're going through this. Remember you're not alone. We're here to help you. Do you need to speak with your trusted professional?",
        "emergency_notification": "Alright, we've notified {emergency_contact} and their team. They will contact you as soon as possible.",
        "resources": "In the meantime, here are some tools that might help you:\n\n1️⃣ Deep breathing: Inhale for 4 seconds, hold for 4 seconds, exhale for 4 seconds.\n2️⃣ Mindfulness: Observe 5 things you can see, 4 things you can touch, 3 things you can hear, 2 things you can smell, and 1 thing you can taste.\n3️⃣ Contact someone you trust to talk.",
        "emergency_services": "If you need immediate help, you can contact emergency services at 112 or the Suicide Prevention Hotline at 024."
    },
    
    "followup": {
        "post_session": "How did you feel after today's session? I'd like to know if there's anything you want to share or any questions that have come up.",
        "feedback_request": "We'd like to know your opinion about your experience so far. Could you rate from 1 to 10 how you're feeling with the therapy?",
        "resources_offer": "Your therapist has recommended some resources that might be useful for you. Would you like to receive them?"
    },
    
    "errors": {
        "general": "I'm sorry, an error has occurred. Please try again later.",
        "processing_info": "I'm sorry, there was a problem processing your information. Could you try again?",
        "processing_specialty": "There was a problem determining the appropriate specialty, but don't worry, we'll continue with the process.",
        "saving_patient": "There was a problem saving your data, but don't worry, we'll continue with the process. Please keep a copy of the information you've provided me.",
        "scheduling": "I'm sorry, there was a problem scheduling the appointment. Please try again or contact us by phone."
    },
    
    "security": {
        "unauthorized": "I'm sorry, I can only accept modification orders from the authorized number. If you are {admin_name}, please send me a message from your personal number ({admin_phone}).",
        "confidentiality": "I'm sorry, I cannot provide information about other patients for confidentiality reasons."
    },
    
    "fields": {
        "name": "full name",
        "phone": "phone number",
        "email": "email address",
        "availability": "availability",
        "language_preference": "preferred language",
        "consultation_reason": "reason for consultation",
        "expectations": "therapy expectations",
        "concerns": "doubts or concerns"
    },
    
    "specialties": {
        "ansiedad": "anxiety",
        "depresion": "depression",
        "trauma": "trauma",
        "pareja": "couple or family therapy",
        "adicciones": "addictions",
        "infantil": "child psychology",
        "adolescentes": "adolescent psychology",
        "general": "general psychology"
    },
    
    "formats": {
        "online": "online (video call)",
        "presencial": "in-person (at our office)"
    },
    
    "confirmation": {
        "yes": "yes",
        "no": "no",
        "maybe": "maybe"
    },
    
    "fallback": {
        "not_understood": "I'm sorry, I didn't understand your message. Could you rephrase it?",
        "need_more_info": "I need a bit more information to help you correctly.",
        "suggest_options": "I can help you with:\n\n- Scheduling or modifying appointments\n- Information about rates and services\n- Answering questions about therapy\n- Contacting your therapist\n\nHow can I help you?"
    }
} 