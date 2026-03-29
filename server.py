# Glossa TTS Server — Free neural voice via edge-tts (Microsoft Neural Voices)
# Usage: python3 server.py
# Endpoint: GET /tts?text=hello&voice=en-US-AvaMultilingualNeural

import asyncio
import hashlib
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

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

async def generate_tts(text, voice, out_path):
    import edge_tts
    comm = edge_tts.Communicate(text, voice)
    await comm.save(out_path)

class TTSHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'ok')
            return

        if parsed.path != '/tts':
            self.send_error(404)
            return

        params = parse_qs(parsed.query)
        text = params.get('text', [''])[0].strip()
        voice = params.get('voice', [DEFAULT_VOICE])[0].strip()

        if not text:
            self.send_error(400, 'Missing text parameter')
            return
        if voice not in ALLOWED_VOICES:
            voice = DEFAULT_VOICE

        mp3_path = cache_path(text, voice)

        if not os.path.exists(mp3_path):
            try:
                asyncio.run(generate_tts(text, voice, mp3_path))
            except Exception as e:
                self.send_error(500, str(e))
                return

        try:
            with open(mp3_path, 'rb') as f:
                data = f.read()
        except Exception as e:
            self.send_error(500, str(e))
            return

        self.send_response(200)
        self.send_header('Content-Type', 'audio/mpeg')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'public, max-age=31536000')
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def log_message(self, fmt, *args):
        text_short = args[0][:80] if args else ''
        print(f'[TTS] {text_short}')

if __name__ == '__main__':
    print(f'Glossa TTS Server')
    print(f'  Port:  {PORT}')
    print(f'  Cache: {CACHE_DIR}')
    print(f'  Voices: {", ".join(sorted(ALLOWED_VOICES))}')
    print(f'  URL:   http://localhost:{PORT}/tts?text=hello')
    server = HTTPServer(('0.0.0.0', PORT), TTSHandler)
    server.serve_forever()
