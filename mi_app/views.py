from django.http import HttpResponse
import openai
import json
import os
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from twilio.rest import Client
from datetime import datetime
from django.conf import settings
from twilio.twiml.messaging_response import MessagingResponse
import requests

# Create your views here.

usuarios = {}

preguntas = [
    "Hola"
    "¿Cuál es tu nombre?",
    "¿Qué tipo de información vas a suministrar?",
    "¿Número del pedido, nombre del proyecto y número de orden de compra?",
    "¿De qué punto es la información que me vas a enviar?",
    "Envíame las fotos/videos del antes del trabajo",
    "Envíame las fotos/videos del después del trabajo",
    "Envíame la foto de la remisión firmada",
    "¿Hubo novedades? Si sí, descríbelas con texto o fotos",
    "¿Tienes algún otro comentario o es el final del informe?"
]


preguntas_con_imagen = {
    5: "antes",
    6: "despues",
    7: "remision"
}

class ChatBotView(APIView):
    
    
    import os
import requests
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from django.http import HttpResponse
from django.conf import settings
from twilio.rest import Client
from . import apps  # Importa el módulo de la app actual para obtener la ruta

usuarios = {}

preguntas = [
    "Hola",
    "¿Cuál es tu nombre?",
    "¿Qué tipo de información vas a suministrar?",
    "¿Número del pedido, nombre del proyecto y número de orden de compra? Separa por medio de comas cada item",
    "¿De qué punto es la información que me vas a enviar?",
    "Envíame las fotos/videos del antes del trabajo",
    "Envíame las fotos/videos del después del trabajo",
    "Envíame la foto de la remisión firmada",
    "¿Hubo novedades? Si sí, descríbelas con texto o fotos",
    "¿Tienes algún otro comentario o es el final del informe?"
]

# Mapeo del estado con carpetas de imágenes
preguntas_con_imagen = {
    5: "antes",
    6: "despues",
    7: "remision"
}


class ChatBotView(APIView):
    @csrf_exempt
    def post(self, request):
        from_number = request.POST.get('From')
        mensaje = request.POST.get('Body')
        num_medias = int(request.POST.get("NumMedia", "0"))

        if not from_number:
            return HttpResponse("Faltan datos", status=400)

        # Inicializar estado del usuario
        if from_number not in usuarios:
            usuarios[from_number] = {
                'estado': 0,
                'respuestas': []
            }

        usuario = usuarios[from_number]
        estado = usuario['estado']

        # Guardar respuesta de texto
        if estado < len(preguntas):
            usuario['respuestas'].append(mensaje)
            usuario['estado'] += 1

        # Si hay imagen y está en pregunta que espera imagen
        if num_medias > 0 and estado in preguntas_con_imagen:
            carpeta = preguntas_con_imagen[estado]

            # Obtener info para el nombre de archivo
            pedido, orden, punto = "sin_pedido", "sin_orden", "sin_punto"

            if len(usuario['respuestas']) >= 4:
                try:
                    partes = [p.strip().replace(" ", "_") for p in usuario['respuestas'][3].split(',')]
                    pedido = partes[0] if len(partes) > 0 else pedido
                    orden = partes[2] if len(partes) > 2 else orden
                except:
                    pass

            if len(usuario['respuestas']) >= 5:
                punto = usuario['respuestas'][4].strip().replace(" ", "_")

            # Ruta dentro de la app
            app_dir = os.path.dirname(__file__)
            ruta_base = os.path.join(app_dir, 'media', carpeta)
            os.makedirs(ruta_base, exist_ok=True)

            for i in range(num_medias):
                media_url = request.POST.get(f'MediaUrl{i}')
                media_type = request.POST.get(f'MediaContentType{i}')
                extension = media_type.split("/")[-1]
                nombre_archivo = f"{pedido}_{orden}_{punto}_{i}.{extension}"
                ruta_completa = os.path.join(ruta_base, nombre_archivo)

                try:
                    response = requests.get(media_url)
                    with open(ruta_completa, 'wb') as f:
                        f.write(response.content)
                except Exception as e:
                    print(f"❌ Error al guardar imagen: {e}")

        # Preparar siguiente mensaje
        if usuario['estado'] < len(preguntas):
            response_message = preguntas[usuario['estado']]
        else:
            resumen = "\n".join(
                [f"{i+1}. {preguntas[i]}\nR// {usuario['respuestas'][i]}" for i in range(len(preguntas))]
            )
            response_message = "✅ ¡Informe completado! Aquí está el resumen:\n\n" + resumen
            usuarios.pop(from_number)

        # Enviar por Twilio
        try:
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TOKEN_TWILIO
            client = Client(account_sid, auth_token)

            client.messages.create(
                from_='whatsapp:+14155238886',
                body=response_message,
                to=from_number
            )
            return HttpResponse("Mensaje enviado correctamente", status=200)

        except Exception as e:
            return HttpResponse(f"Error al enviar mensaje: {str(e)}", status=500)
    