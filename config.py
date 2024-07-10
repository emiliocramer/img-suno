import os

DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
SUNO_API_URL = os.environ.get('SUNO_API_URL')

required_vars = ['DISCORD_TOKEN', 'OPENAI_API_KEY', 'SUNO_API_URL']
missing_vars = [var for var in required_vars if not locals().get(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Other configuration settings
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
TIMEOUT = int(os.getenv('TIMEOUT', 300))
