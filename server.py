# Glossa TTS Server — Free neural voice via edge-tts
# Fully async with aiohttp — works on Render free tier
import asyncio
import hashlib
import os
from aiohttp import web
import edge_tts

CACHE_DIR = os.environ.get('TTS_CACHE_DIR', os.path.expanduser('~/glossa-tts-cache'))
PORT = int(os.environ.get('PORT', 5111))
DEFAULT_VOICE = 'en-US-AvaMultilingualNeural'
ALLOWED_VOICES = {
    'en-US-AvaMultilingualNeural',
    'en-GB-SoniaNeural',
    'en-US-AndrewNeural',
}

os.makedirs(CACHE_DIR, exist_ok=True)

def cache_path(text, voice):
    key = hashlib.md5(f'{voice}:{text}'.encode()).hexdigest()
    return os.path.join(CACHE_DIR, f'{key}.mp3')

async def handle_health(request):
    return web.Response(text='ok')

async def handle_tts(request):
    text = request.query.get('text', '').strip()
    voice = request.query.get('voice', DEFAULT_VOICE).strip()
    if not text:
        return web.Response(status=400, text='Missing text parameter')
    if voice not in ALLOWED_VOICES:
        voice = DEFAULT_VOICE

    mp3 = cache_path(text, voice)

    if not os.path.exists(mp3):
        try:
            comm = edge_tts.Communicate(text, voice)
            await comm.save(mp3)
        except Exception as e:
            return web.Response(status=500, text=str(e))

    try:
        with open(mp3, 'rb') as f:
            data = f.read()
    except Exception as e:
        return web.Response(status=500, text=str(e))

    return web.Response(
        body=data,
        content_type='audio/mpeg',
        headers={
            'Access-Control-Allow-Origin': '*',
            'Cache-Control': 'public, max-age=31536000',
        },
    )

async def handle_options(request):
    return web.Response(
        status=204,
        headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': '*',
        },
    )

app = web.Application()
app.router.add_get('/health', handle_health)
app.router.add_get('/tts', handle_tts)
app.router.add_route('OPTIONS', '/tts', handle_options)

if __name__ == '__main__':
    print(f'Glossa TTS Server (async)')
    print(f'  Port:  {PORT}')
    print(f'  Cache: {CACHE_DIR}')
    print(f'  Voices: {", ".join(sorted(ALLOWED_VOICES))}')
    web.run_app(app, host='0.0.0.0', port=PORT)
