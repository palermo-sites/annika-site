// Generates the site's original SVG gown illustrations into public/images (no third-party imagery).
import { writeFileSync, mkdirSync } from 'node:fs';
mkdirSync('public/images', { recursive: true });
const bodices = {
  offshoulder: 'M170 150 C185 140 215 140 230 150 L250 145 L245 165 C235 175 225 205 222 240 L178 240 C175 205 165 175 155 165 L150 145 Z',
  sweetheart: 'M175 160 C180 148 195 148 200 158 C205 148 220 148 225 160 L222 240 L178 240 Z',
  vneck: 'M172 145 L200 200 L228 145 L226 240 L174 240 Z',
  square: 'M172 155 L228 155 L226 240 L174 240 Z',
  sleeve: 'M172 145 L200 190 L228 145 L226 240 L174 240 Z',
  halter: 'M190 130 L210 130 L228 170 L226 240 L174 240 L172 170 Z',
};
const skirts = {
  aline: 'M178 240 L222 240 C250 330 290 430 320 520 L80 520 C110 430 150 330 178 240 Z',
  mermaid: 'M178 240 L222 240 C232 320 228 380 222 420 C250 460 290 500 320 520 L80 520 C110 500 150 460 178 420 C172 380 168 320 178 240 Z',
  ball: 'M178 240 L222 240 C300 300 345 420 355 520 L45 520 C55 420 100 300 178 240 Z',
  column: 'M178 240 L222 240 C226 330 232 430 250 520 L150 520 C168 430 174 330 178 240 Z',
  flowing: 'M178 240 L222 240 C255 320 270 420 300 520 C250 505 150 505 100 520 C130 420 145 320 178 240 Z',
  train: 'M178 240 L222 240 C232 340 250 440 340 520 L120 520 C150 440 168 340 178 240 Z',
};
const pieces = {
  aurelia: ['offshoulder', 'aline', '#f3e3df'], seraphine: ['sleeve', 'mermaid', '#efe4dc'], celeste: ['sweetheart', 'ball', '#f6ece2'],
  noor: ['vneck', 'train', '#e3dedb'], wren: ['halter', 'flowing', '#f2e6e1'], margot: ['square', 'aline', '#eee6da'],
  sketch: ['vneck', 'mermaid', '#faf6f0'], lace: ['sweetheart', 'column', '#f4e8e4'], silk: ['square', 'train', '#efe7df'],
  veil: ['offshoulder', 'flowing', '#f6eeea'], structure: ['halter', 'ball', '#ece6e1'],
};
for (const [name, [b, s, bg]] of Object.entries(pieces)) {
  const sketch = name === 'sketch' || ['lace', 'silk', 'veil', 'structure'].includes(name);
  const fill = sketch ? 'none' : 'url(#g)';
  const stroke = sketch ? '#5b5552' : '#d9c7bd';
  const lines = sketch ? `<g stroke="#b9a59c" stroke-width="0.8" opacity="0.6">${Array.from({ length: 9 }, (_, i) => `<path d="M${120 + i * 20} 520 Q${190 + i * 3} 380 ${190 + i * 2.5} 250" fill="none"/>`).join('')}</g>` : '';
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 560" role="img" aria-label="Illustration of a ${s} wedding gown">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fffdf8"/><stop offset="0.6" stop-color="#f7efe6"/><stop offset="1" stop-color="#e9dccf"/></linearGradient>
<radialGradient id="l" cx="0.3" cy="0.2" r="0.9"><stop offset="0" stop-color="#ffffff" stop-opacity="0.7"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/></radialGradient></defs>
<rect width="400" height="560" fill="${bg}"/><rect width="400" height="560" fill="url(#l)"/>
<ellipse cx="200" cy="528" rx="170" ry="10" fill="#000" opacity="0.05"/>
<path d="M200 70 L200 130" stroke="#7a6a62" stroke-width="3"/><circle cx="200" cy="66" r="6" fill="#7a6a62"/>
<path d="${skirts[s]}" fill="${fill}" stroke="${stroke}" stroke-width="${sketch ? 1.4 : 1}"/>${lines}
<path d="${bodices[b]}" fill="${sketch ? 'none' : '#fffaf3'}" stroke="${stroke}" stroke-width="${sketch ? 1.4 : 1}"/>
<path d="M176 240 Q200 248 224 240" stroke="${sketch ? '#5b5552' : '#e4cfc4'}" stroke-width="2" fill="none"/>
</svg>
`;
  writeFileSync(`public/images/${name}.svg`, svg);
}
writeFileSync('public/images/og.svg', `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630"><rect width="1200" height="630" fill="#f8f3ec"/><text x="600" y="300" font-family="Georgia, serif" font-size="84" text-anchor="middle" fill="#2f2b2a">Annika Palermo</text><text x="600" y="370" font-family="Georgia, serif" font-size="30" letter-spacing="8" text-anchor="middle" fill="#a77d73">BRIDAL COUTURE · SAMPLE SITE</text></svg>\n`);
console.log('art written');
