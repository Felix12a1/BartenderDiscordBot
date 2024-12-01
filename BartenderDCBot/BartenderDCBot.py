import discord
from discord.ext import commands
from flask import Flask, request, jsonify
import asyncio
import aiohttp
from threading import Thread
import os
from dotenv import load_dotenv

# Cargar las variables del archivo .env
load_dotenv()


# Configuración del bot
intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Configuración de Flask
app = Flask(__name__)

# Canal de Discord donde enviar los mensajes
DISCORD_CHANNEL_ID = 1312695472359735328  # Reemplaza con el ID de tu canal
# Obtener el token desde la variable de entorno
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Verificar si el token se cargó correctamente
print("Discord Token cargado:", DISCORD_TOKEN)

# Webhook de GitHub
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json

    # Información del payload
    repo_name = data['repository']['name']  # Nombre del repositorio
    action_type = data['action'] if 'action' in data else 'Push'  # Tipo de acción (por defecto es 'Push')
    branch = data['ref'].split('/')[-1]  # Nombre de la branch
    for commit in data['commits']:
        author = commit['author']['name']
        timestamp = commit['timestamp']
        title = commit['message'].split("\n")[0]
        description = "\n".join(commit['message'].split("\n")[1:]) if len(commit['message'].split("\n")) > 1 else None

        # Si no hay descripción, usar "No se ha brindado una descripción" en cursiva
        if not description:
            description = "*No se ha brindado una descripción*"

        # URL del commit en el repositorio
        commit_url = commit['url']

        # Enviar mensaje al canal de Discord
        asyncio.run_coroutine_threadsafe(
            send_to_discord(repo_name, action_type, branch, author, timestamp, title, description, commit_url),
            bot.loop
        )

    return jsonify({"status": "success"}), 200

# Enviar mensaje a Discord
async def send_to_discord(repo_name, action_type, branch, author, timestamp, title, description, commit_url):
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        await channel.send(
            f"🚀 **Acción realizada en el repositorio `{repo_name}`**\n\n"
            f"**Tipo de acción:** `{action_type}`\n"
            f"**Branch afectada:** `{branch}`\n"
            f"**Commit Hash:** `{commit_url.split('/')[-1]}`\n"
            f"**Autor:** `{author}`\n"
            f"**Fecha:** `{timestamp}`\n\n"
            f"🔹 **Título del commit:** {title}\n"
            f"🔹 **Descripción:** {description}\n\n"
            f"🔗 **Enlace al commit:** [Ver commit en GitHub]({commit_url})"
        )

# Función para hacer un ping a la propia aplicación
async def ping_self():
    url = "http://127.0.0.1:8080"  # URL de la aplicación Flask en Replit (ajustar si es necesario)
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    print(f"Ping exitoso: {response.status}")
        except Exception as e:
            print(f"Error al hacer ping: {e}")

        await asyncio.sleep(300)  # Esperar 5 minutos antes de hacer el siguiente ping

# Iniciar Flask en un hilo separado
def run_flask():
    app.run(host="0.0.0.0", port=8080)

# Evento de inicio del bot
@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

    # Enviar mensaje de inicio al canal de Discord
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        await channel.send(f"¡El bot {bot.user.name} se ha iniciado exitosamente!")


# Función principal
async def main():
    # Iniciar Flask en un hilo separado
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    # Iniciar el task de ping
    ping_task = asyncio.create_task(ping_self())

    # Iniciar el bot
    await bot.start(DISCORD_TOKEN)

# Ejecutar la función principal
asyncio.run(main())
