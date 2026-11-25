"""Rebuild local pixel assets and the banner: python scripts/build-profile.py.

Pixel font and original glyphs: Celio Junior, retro-profile-readme (MIT).
"""
from pathlib import Path
import html
import json
import re
import textwrap
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
GLYPHS = json.loads((ROOT / 'scripts/pixel-glyphs.json').read_text())
FONT = GLYPHS['font_5x7']
FONT[':'] = ['.', '#', '.', '.', '#', '.', '.']
PAPER, INK, BLUE, YELLOW = '#fbfaf6', '#1d1c1a', '#1846b8', '#f2c230'


def rect(x, y, w, h, color):
    return f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="{color}"/>'


def pixels(rows, x, y, scale=1):
    colors = {'#': INK, '*': BLUE, 'o': YELLOW}
    return ''.join(rect(x + col * scale, y + row * scale, scale, scale, colors[c])
                   for row, line in enumerate(rows) for col, c in enumerate(line) if c in colors)


def text(value, x, y, scale=1):
    result = ''
    for c in value.upper():
        assert c in FONT, f'Unsupported pixel character: {c}'
        result += ''.join(rect(x + col * scale, y + row * scale, scale, scale, INK)
                          for row, line in enumerate(FONT[c]) for col, p in enumerate(line) if p == '#')
        x += (len(FONT[c][0]) + 1) * scale
    return result


def svg(w, h, body, title, description=''):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" shape-rendering="crispEdges" role="img" '
            f'aria-labelledby="title desc"><title id="title">{html.escape(title)}</title>'
            f'<desc id="desc">{html.escape(description or title)}</desc>{body}</svg>\n')


def card(x, y, w, h):
    return (rect(x + 1, y, w - 2, h, INK) + rect(x, y + 1, w, h - 2, INK)
            + rect(x + 1, y + 1, w - 2, h - 2, PAPER)
            + rect(x + 1, y + 1, w - 2, 1, '#ffffff')
            + rect(x + w - 2, y + 1, 1, h - 2, '#b9b5aa')
            + rect(x + 1, y + h - 2, w - 2, 1, '#b9b5aa'))


def build():
    cfg = json.loads((ROOT / 'profile.json').read_text(encoding='utf-8'))
    for item in cfg['stack']:
        rows = item.get('glyph') or GLYPHS['icons'][item['id']]
        assert 0 < len(rows) <= 14 and len({len(row) for row in rows}) == 1
        assert 0 < len(rows[0]) <= 14 and set(''.join(rows)) <= set('.#*o')
        body = card(2, 2, 16, 16) + pixels(rows, 2 + (16 - len(rows[0])) // 2, 2 + (16 - len(rows)) // 2)
        # Match the existing 60px tiles, drawing on an integer 20x20 grid.
        image = svg(60, 60, f'<g transform="scale(3)">{body}</g>', item['label'])
        (ROOT / f'imgs/icons/lang-{item["id"]}.svg').write_text(image, encoding='utf-8')

    computer = [
        '.############.', '##oooooooooo##', '#o**********o#',
        '#o*##*******o#', '#o***##*****o#', '#o*##*******o#',
        '#o*****###**o#', '#o**********o#', '##oooooooooo##',
        '.############.', '......##......', '...########...',
        '..##########..',
    ]
    lines = []
    for paragraph in cfg['window']['paragraphs']:
        lines += textwrap.wrap(' '.join(paragraph), width=68) + ['']
    if not lines[-1]:
        lines.pop()
    body_y = 236
    height = body_y + len(lines) * 23 + 72
    body = rect(6, 6, 894, height - 6, INK) + card(0, 0, 894, height - 6)
    body += rect(18, 18, 858, 30, YELLOW) + text('GABRZB / PROFILE', 30, 27, 2)
    body += text(cfg['name'], 36, 78, 7) + pixels(computer, 744, 66, 8)
    body += text('FULL STACK DEVELOPER / BRAZIL', 38, 148, 2)
    body += rect(18, 196, 858, height - 220, INK) + rect(21, 199, 852, height - 226, PAPER)
    body += rect(21, 199, 852, 25, '#e6e2d8') + text('ABOUT.TXT', 36, 207, 1.5)
    for x, color in [(820, BLUE), (838, YELLOW), (856, INK)]:
        body += rect(x, 207, 9, 9, color)
    for i, line in enumerate(lines):
        assert sum(len(FONT[c][0]) + 1 for c in line.upper()) * 1.8 <= 810, 'Banner line exceeds window'
        body += text(line, 38, body_y + i * 23, 1.8)
    body += text('- GABRZB', 38, body_y + len(lines) * 23 + 8, 1.8)
    description = ' '.join(' '.join(p) for p in cfg['window']['paragraphs'])
    (ROOT / 'imgs/banner.svg').write_text(svg(900, height, body,
        'Gabriel Zaniqueli Beltrame - Full Stack Developer', description), encoding='utf-8')
    md_path = ROOT / 'README.md'
    md = md_path.read_text(encoding='utf-8')
    banner = ('<p align="center">\n  <img src="./imgs/banner.svg" '
              'alt="Gabriel Zaniqueli Beltrame — Full Stack Developer, Brazil. '
              'Building web applications with Angular, React and Spring Boot. '
              'Open to collaboration, freelance projects and new opportunities." width="900">\n</p>')
    if md.startswith('```text'):
        md = re.sub(r'\A```text\n.*?\n```', lambda _: banner, md, count=1, flags=re.S)
    else:
        md, count = re.subn(r'\A<p align="center">.*?</p>', lambda _: banner, md, count=1, flags=re.S)
        assert count == 1, 'Expected profile banner at the start of README'
    md_path.write_text(md, encoding='utf-8')
    for path in re.findall(r'src="\./([^"]+)"', md):
        assert (ROOT / path).is_file(), f'Missing image: {path}'
        if path.endswith('.svg'):
            ET.parse(ROOT / path)
    print('Built banner and all 19 technology icons; SVGs and image references verified.')


if __name__ == '__main__':
    build()
