# Curadoria semanal de manchetes de CX e Contact Center (somente titulo, veiculo, data e link).
import urllib.request, urllib.parse, xml.etree.ElementTree as ET, json, html, datetime, email.utils, pathlib, re
BASE = pathlib.Path('.')
Q = ['"contact center" OR "call center"',
     '"experiência do cliente" OR "customer experience" OR "customer success"',
     'SAC atendimento consumidor Senacon OR Procon OR "Reclame Aqui"']
FEEDS = [('Consumidor Moderno', 'https://consumidormoderno.com.br/feed/')]
for q in Q:
    FEEDS.append(('Google Notícias', 'https://news.google.com/rss/search?' + urllib.parse.urlencode({'q': q + ' when:7d', 'hl': 'pt-BR', 'gl': 'BR', 'ceid': 'BR:pt-419'})))
UA = {'User-Agent': 'QualiCX-Brasil-curadoria/1.0 (+https://qualicx-brasil.github.io/)'}
KEY = re.compile(r'(atendimento|cliente|consumidor|CX|contact center|call center|SAC|experiência|customer|ouvidoria|NPS|chatbot|omnichannel)', re.I)
RUIDO = re.compile(r'(gasolina|combust|diesel|DNA|paternidade|vacina|eleiç|futebol|loteria|preço d[aoe]s? |vaga|emprego|salário|contrata|concurso|currículo)', re.I)
now = datetime.datetime.now(datetime.timezone.utc)
items, seen = [], set()
for nome, url in FEEDS:
    try:
        data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
        root = ET.fromstring(data)
    except Exception as e:
        print('falhou', nome, e); continue
    for it in root.iter('item'):
        t = (it.findtext('title') or '').strip(); l = (it.findtext('link') or '').strip()
        src = (it.findtext('source') or nome).strip()
        sel = it.find('source')
        dom = urllib.parse.urlparse(sel.get('url') if sel is not None and sel.get('url') else (l if nome != 'Google Notícias' else '')).netloc.replace('www.', '')
        if nome == 'Google Notícias' and ' - ' in t and src != nome:
            t = t.rsplit(' - ', 1)[0]
        try: d = email.utils.parsedate_to_datetime(it.findtext('pubDate'))
        except Exception: d = now
        if d.tzinfo is None: d = d.replace(tzinfo=datetime.timezone.utc)
        if (now - d).days > 10 or not t or not l: continue
        if not KEY.search(t) or RUIDO.search(t) or src.lower() in ('instagram','facebook','youtube','tiktok'): continue
        k = re.sub(r'\W+', '', t.lower())[:80]
        if k in seen: continue
        seen.add(k); items.append({'titulo': t, 'fonte': src, 'data': d.strftime('%Y-%m-%d'), 'link': l, 'dominio': dom})
items.sort(key=lambda x: x['data'], reverse=True); items = items[:40]
(BASE/'data').mkdir(exist_ok=True)
(BASE/'data'/'noticias.json').write_text(json.dumps({'atualizado': now.strftime('%Y-%m-%d'), 'itens': items}, ensure_ascii=False, indent=1))
print('noticias:', len(items))
