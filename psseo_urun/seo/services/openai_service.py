"""
OpenAI (ChatGPT) ile SEO içerik üretimi.
PrestaShop 1.7 uyumlu HTML çıktı döner.
Aynı prompt şablonlarını ai_service ile paylaşır.
"""
import openai
from django.conf import settings
from .ai_service import _PROMPTS, _urun_bilgi_metni


def uret_openai_icerik(urun, tip):
    """
    ChatGPT (gpt-4o-mini) ile istenen tipte SEO içerik üretir.
    Dönen değer: (icerik_str, model_adi_str)
    """
    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    if not api_key:
        raise ValueError('OPENAI_API_KEY ayarlanmamış. .env dosyasına ekleyin.')

    prompt_sablonu = _PROMPTS.get(tip)
    if not prompt_sablonu:
        raise ValueError(f'Bilinmeyen içerik tipi: {tip}')

    urun_bilgi = _urun_bilgi_metni(urun)
    prompt     = prompt_sablonu.format(urun_bilgi=urun_bilgi)
    model_adi  = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')

    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model_adi,
        max_tokens=2048,
        messages=[{'role': 'user', 'content': prompt}],
    )
    icerik = response.choices[0].message.content.strip()

    if icerik.startswith('```'):
        satirlar = icerik.splitlines()
        icerik   = '\n'.join(satirlar[1:-1] if satirlar[-1] == '```' else satirlar[1:]).strip()

    return icerik, model_adi
