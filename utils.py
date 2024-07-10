import logging
from openai import OpenAI
import aiohttp
import asyncio
from config import OPENAI_API_KEY, SUNO_API_URL, MAX_RETRIES, TIMEOUT
from exceptions import ImageProcessingError, SongGenerationError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)


async def get_image_description(image_url: str, prompt: str) -> str:
    """
    Get image description using OpenAI's API.

    Args:
        image_url (str): URL of the image to process.
        prompt (str): Prompt for image description.

    Returns:
        str: Generated description of the image.

    Raises:
        ImageProcessingError: If there's an error processing the image.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ],
                }
            ]
        )
        return response.choices[0].message.content[:200]
    except Exception as e:
        logger.error(f"Error in get_image_description: {e}", exc_info=True)
        raise ImageProcessingError("Failed to process the image") from e


async def generate_song(description: str) -> str:
    """
    Generate a song using the Suno API.

    Args:
        description (str): Description to base the song on.

    Returns:
        str: URL of the generated song.

    Raises:
        SongGenerationError: If there's an error generating the song.
    """

    async def make_request():
        try:
            payload = {
                "prompt": description,
                "make_instrumental": False,
                "wait_audio": True
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{SUNO_API_URL}/api/generate", json=payload) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logger.error(f"Error in generate_song request: {e}", exc_info=True)
            raise

    for attempt in range(MAX_RETRIES):
        try:
            data = await make_request()
            audio_ids = f"{data[0]['id']},{data[1]['id']}"

            async def check_status():
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{SUNO_API_URL}/api/get?ids={audio_ids}") as info:
                        info_data = await info.json()
                        if info_data[0]["status"] == 'streaming':
                            return info_data[0]['audio_url']
                return None

            start_time = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start_time < TIMEOUT:
                result = await check_status()
                if result:
                    return result
                await asyncio.sleep(5)

            raise SongGenerationError("Timed out waiting for song generation")
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                logger.error(f"Failed to generate song after {MAX_RETRIES} attempts: {e}", exc_info=True)
                raise SongGenerationError("Failed to generate the song") from e
            logger.warning(f"Attempt {attempt + 1} failed, retrying...")
            await asyncio.sleep(2 ** attempt)