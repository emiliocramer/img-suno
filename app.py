import os
import discord
from discord.ext import commands
import aiohttp
from openai import OpenAI
import requests
import time
import ssl

DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
SUNO_API_URL = os.environ.get('SUNO_API_URL')

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN is not set in the environment variables")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables")
if not SUNO_API_URL:
    raise ValueError("SUNO_API_URL is not set in the environment variables")


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

connector = aiohttp.TCPConnector(ssl=ssl_context)
bot = commands.Bot(command_prefix='!', intents=intents, connector=connector)
client = OpenAI(api_key=OPENAI_API_KEY)


async def get_image_description(image_url):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe the main mood and atmosphere of this image in 2-3 sentences. Be very concise. DESCRIBE IT IN A WAY THAT IF YOU WERE TALKING TO A ROBOT ABOUT IT, HE WOULD BE ABLE TO CREATE A SONG DESCRIBING AND REPRESENTING THE IMAGE BASED ON YOUR DESCRIPTION"},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ],
                }
            ]
        )
        description = response.choices[0].message.content
        # Strictly limit to 200 characters
        return description[:200]
    except Exception as e:
        print(f"Error in get_image_description: {e}")
        print(f"Error type: {type(e)}")
        print(f"Image URL: {image_url}")
        return None


async def generate_song(description):
    """Generate a song using unofficial Suno API based on the image description."""
    try:
        payload = {
            "prompt": description,
            "make_instrumental": False,
            "wait_audio": True
        }
        full_url = f"{SUNO_API_URL}/api/generate"
        print(f"Attempting to call Suno API at: {full_url}")
        print(f"With payload: {payload}")

        response = requests.post(full_url, json=payload)
        print(f"Suno API Response Status: {response.status_code}")
        print(f"Suno API Response Headers: {response.headers}")
        print(f"Suno API Response Content: {response.text}")

        response.raise_for_status()
        data = response.json()

        # Wait for the audio to be ready
        audio_ids = f"{data[0]['id']},{data[1]['id']}"
        for _ in range(60):  # Wait up to 5 minutes
            info_url = f"{SUNO_API_URL}/api/get?ids={audio_ids}"
            print(f"Checking audio status at: {info_url}")
            info = requests.get(info_url)
            print(f"Audio Status Response: {info.text}")
            info_data = info.json()
            if info_data[0]["status"] == 'streaming':
                return info_data[0]['audio_url']
            time.sleep(5)

        return None
    except requests.exceptions.RequestException as e:
        print(f"Error in generate_song: {e}")
        print(f"Response status code: {e.response.status_code if e.response else 'N/A'}")
        print(f"Response content: {e.response.text if e.response else 'N/A'}")
        return None


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')


@bot.command(name='create_song')
async def create_song(ctx):
    """Command to create a song from an attached image."""
    if not ctx.message.attachments:
        await ctx.send("Please attach an image to your message.")
        return

    image = ctx.message.attachments[0]
    if not image.content_type.startswith('image'):
        await ctx.send("The attached file is not an image.")
        return

    await ctx.send("Processing your image... This may take a moment.")

    description = await get_image_description(image.url)
    if not description:
        await ctx.send("Sorry, I couldn't generate a description for this image.")
        return

    print(f"Generated description: {description}")  # Debug print
    print(f"Description length: {len(description)} characters")  # Debug print

    await ctx.send("Generating a song based on the image... This may take a few minutes.")

    song_url = await generate_song(description)
    if not song_url:
        await ctx.send("Sorry, I couldn't generate a song based on this image. The description might have been too long or complex.")
        return

    await ctx.send(f"Here's your generated song: {song_url}")


# Run the bot
bot.run(DISCORD_TOKEN)
