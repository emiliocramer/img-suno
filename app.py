import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import ssl
import logging

from config import DISCORD_TOKEN, LOG_LEVEL
from exceptions import ImageProcessingError, SongGenerationError
from utils import get_image_description, generate_song

logging.basicConfig(level=getattr(logging, LOG_LEVEL),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

connector = aiohttp.TCPConnector(ssl=ssl_context)
bot = commands.Bot(command_prefix='!', intents=intents, connector=connector)


@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}", exc_info=True)


@bot.tree.command(name="create_song", description="Create a song based on an uploaded image")
@app_commands.describe(image="The image to base the song on")
async def create_song(interaction: discord.Interaction, image: discord.Attachment):
    await interaction.response.defer(thinking=True)

    if not image.content_type.startswith('image'):
        await interaction.followup.send("The attached file is not an image.")
        return

    try:
        prompt = "Describe the main mood and atmosphere of this image in 2-3 sentences. Be very concise. DESCRIBE IT IN A WAY THAT IF YOU WERE TALKING TO A ROBOT ABOUT IT, HE WOULD BE ABLE TO CREATE A SONG DESCRIBING AND REPRESENTING THE IMAGE BASED ON YOUR DESCRIPTION"
        description = await get_image_description(image.url, prompt)
        song_url = await generate_song(description)
        await interaction.followup.send(f"Here's your generated song: {song_url}")
    except (ImageProcessingError, SongGenerationError) as e:
        await interaction.followup.send(f"An error occurred: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in create_song: {e}", exc_info=True)
        await interaction.followup.send("An unexpected error occurred. Please try again later.")


@bot.tree.command(name="roast_me", description="Create a roast song based on an uploaded image")
@app_commands.describe(image="The image to base the roast song on")
async def roast_me(interaction: discord.Interaction, image: discord.Attachment):
    await interaction.response.defer(thinking=True)

    if not image.content_type.startswith('image'):
        await interaction.followup.send("The attached file is not an image.")
        return

    try:
        prompt = "Describe this image in a humorous and slightly mocking way. Be witty and clever, but not cruel. Focus on creating a funny, roast-like description that could be turned into a comedic song. Keep it light-hearted and entertaining."
        description = await get_image_description(image.url, prompt)
        song_url = await generate_song(description)
        await interaction.followup.send(f"Here's your generated roast song: {song_url}")
    except (ImageProcessingError, SongGenerationError) as e:
        await interaction.followup.send(f"An error occurred: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in roast_me: {e}", exc_info=True)
        await interaction.followup.send("An unexpected error occurred. Please try again later.")


# Run the bot
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)