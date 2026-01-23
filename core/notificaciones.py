import requests
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags


# --- 1. ENVIAR POR TELEGRAM ---
def enviar_telegram(token, chat_id, mensaje):
    if not token or not chat_id:
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=data, timeout=5)
        return True
    except Exception as e:
        print(f"Error Telegram: {e}")
        return False

# --- 2. ENVIAR POR DISCORD ---
def enviar_discord(webhook_url, mensaje):
    if not webhook_url:
        return False

    data = {
        "content": mensaje
    }
    try:
        requests.post(webhook_url, json=data, timeout=5)
        return True
    except Exception as e:
        print(f"Error Discord: {e}")
        return False

# --- 3. ENVIAR POR EMAIL (Dinámico) ---
def enviar_email_dinamico(usuario_perfil, asunto, mensaje_html):
    # Aquí leeríamos la configuración del usuario si la hubiéramos puesto en el modelo.
    # Como por seguridad Django prefiere usar settings.py para el email global,
    # usaremos la configuración por defecto del servidor para enviar el correo AL usuario.
    
    # Nota: Para que esto funcione, necesitamos configurar el SMTP en settings.py
    # o pedirle al usuario sus credenciales SMTP en el modelo.
    # Por simplicidad en esta fase, asumiremos que usas el correo configurado en el sistema.
    
    try:
        msg = EmailMultiAlternatives(
            subject=asunto,
            body=strip_tags(mensaje_html),
            from_email='legalwatch@tuservidor.com',
            to=[usuario_perfil.user.email]
        )
        msg.attach_alternative(mensaje_html, "text/html")
        msg.send()
        return True
    except Exception as e:
        print(f"Error Email: {e}")
        return False