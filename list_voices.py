import asyncio
import edge_tts

async def main():
    voices = await edge_tts.list_voices()
    for v in voices:
        if v['Locale'].startswith('en-'):
            name = v['ShortName']
            gender = v['Gender']
            tags = v.get('VoiceTag', {}).get('VoicePersonalities', '')
            print(f"{name:40s} {gender:8s} {tags}")

asyncio.run(main())
