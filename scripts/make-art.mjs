// Original placeholder drawings for the dress sketchbook. No third-party imagery.
// Writes SVG pairs to public/images. When RESVG_MODULE points at @resvg/resvg-js
// and ffmpeg is on the PATH, also writes a short muted preview clip per dress.
import { mkdirSync, writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';

const imagesDir = 'public/images';
const videosDir = 'public/videos';
mkdirSync(imagesDir, { recursive: true });
mkdirSync(videosDir, { recursive: true });

const pencil = '#6d645c';
const ink = '#7a7067';
const card = '#fffdf8';

/** @type {Array<Record<string, any>>} */
const dresses = [
  {
    id: 'midnight-silk-gown',
    title: 'Midnight Silk Gown',
    accent: '#B5D0EA',
    cloth:
      'M70 96 C70 70 88 58 100 82 C112 58 130 70 130 96 C132 124 126 146 122 160 C156 206 176 258 178 294 L22 294 C24 258 44 206 78 160 C74 146 68 124 70 96 Z',
    seams: ['M78 160 Q100 168 122 160'],
  },
  {
    id: 'linen-sundress',
    title: 'Linen Sundress',
    accent: '#E6D392',
    straps: ['M84 50 L86 88', 'M116 50 L114 88'],
    cloth:
      'M80 88 C80 74 90 78 100 92 C110 78 120 74 120 88 L124 142 C150 170 160 198 162 222 L38 222 C40 198 50 170 76 142 Z',
    seams: ['M78 142 Q100 148 122 142'],
  },
  {
    id: 'rosewater-tea-dress',
    title: 'Rosewater Tea Dress',
    accent: '#F3C3D0',
    sleeves: [
      'M74 90 C46 78 40 114 74 122 C62 110 64 98 74 90 Z',
      'M126 90 C154 78 160 114 126 122 C138 110 136 98 126 90 Z',
    ],
    cloth:
      'M78 92 C86 78 114 78 122 92 L118 150 C144 184 154 220 156 258 L44 258 C46 220 56 184 82 150 Z',
    seams: ['M84 150 Q100 156 116 150'],
    detail: '52 60 96 108',
  },
  {
    id: 'velvet-opera-sheath',
    title: 'Velvet Opera Sheath',
    accent: '#D3C0E6',
    cloth:
      'M78 64 Q100 52 122 64 L116 150 C122 198 124 250 126 294 L74 294 C76 250 78 198 84 150 Z',
    seams: ['M86 150 Q100 154 114 150'],
  },
  {
    id: 'chiffon-garden-maxi',
    title: 'Chiffon Garden Maxi',
    accent: '#B7DCCB',
    straps: ['M90 46 L92 80', 'M110 46 L108 80'],
    cloth:
      'M84 80 C90 96 110 96 116 80 L108 114 C152 172 170 246 172 294 L28 294 C30 246 48 172 92 114 Z',
    seams: ['M92 114 Q100 118 108 114'],
  },
  {
    id: 'ivory-satin-slip',
    title: 'Ivory Satin Slip',
    accent: '#F4D2BA',
    straps: ['M92 44 L94 74', 'M108 44 L106 74'],
    cloth:
      'M86 74 L100 102 L114 74 L118 158 C124 208 126 252 128 278 L72 278 C74 252 76 208 82 158 Z',
    seams: ['M84 158 Q100 164 116 158'],
  },
];

const strokeAttrs = (sketch, width) =>
  `fill="none" stroke="${sketch ? pencil : ink}" stroke-width="${width}" stroke-linecap="round" stroke-linejoin="round"${sketch ? ' stroke-dasharray="4.2 3.1"' : ''}`;

function drawing(dress, { sketch, viewBox = '0 0 200 300', backdrop = false }) {
  const cloth = sketch
    ? `<path d="${dress.cloth}" ${strokeAttrs(true, 2)}/>`
    : `<path d="${dress.cloth}" fill="${dress.accent}" stroke="${ink}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>`;
  const sleeves = (dress.sleeves ?? [])
    .map((d) =>
      sketch
        ? `<path d="${d}" ${strokeAttrs(true, 2)}/>`
        : `<path d="${d}" fill="${dress.accent}" stroke="${ink}" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/>`,
    )
    .join('');
  const straps = (dress.straps ?? []).map((d) => `<path d="${d}" ${strokeAttrs(sketch, sketch ? 2 : 2.3)}/>`).join('');
  const seams = (dress.seams ?? [])
    .map((d) => `<path d="${d}" ${strokeAttrs(sketch, 1.4)}/>`)
    .join('');
  const label = `${dress.title}${sketch ? ' pencil sketch' : ' finished study'}`;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${viewBox}" role="img">
<title>${label}</title>
${backdrop ? `<rect width="200" height="300" fill="${card}"/>` : ''}
${sleeves}${cloth}${straps}${seams}
</svg>
`;
}

for (const dress of dresses) {
  writeFileSync(`${imagesDir}/${dress.id}-sketch.svg`, drawing(dress, { sketch: true }));
  writeFileSync(`${imagesDir}/${dress.id}.svg`, drawing(dress, { sketch: false }));
  if (dress.detail) {
    writeFileSync(
      `${imagesDir}/${dress.id}-detail.svg`,
      drawing(dress, { sketch: false, viewBox: dress.detail }),
    );
  }
}

writeFileSync(
  `${imagesDir}/og.svg`,
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630">
<defs>
<pattern id="dots" width="14" height="14" patternUnits="userSpaceOnUse">
<circle cx="1.2" cy="1.2" r="0.85" fill="#c9b79d"/>
</pattern>
</defs>
<rect width="1200" height="630" fill="#f4efe6"/>
<rect width="1200" height="630" fill="url(#dots)"/>
<text x="600" y="300" text-anchor="middle" font-family="Caveat, cursive" font-size="108" font-weight="600" fill="#6f4458">Annika Palermo</text>
<text x="600" y="378" text-anchor="middle" font-family="Source Serif 4, Georgia, serif" font-style="italic" font-size="32" fill="#6e655c">from first pencil line to finished frock</text>
</svg>
`,
);

console.log(`wrote ${dresses.length} dress pairs`);

const modulePath = process.env.RESVG_MODULE;
if (!modulePath) {
  console.log('SVG only. Set RESVG_MODULE to also render preview videos.');
} else {
  const { Resvg } = await import(modulePath);
  const fontFiles = process.env.OG_FONT ? [process.env.OG_FONT] : [];
  const renderPng = (svg, width) => {
    const resvg = new Resvg(svg, {
      fitTo: { mode: 'width', value: width },
      font: { loadSystemFonts: true, fontFiles, defaultFontFamily: 'Caveat' },
      background: card,
    });
    return resvg.render().asPng();
  };

  const { readFileSync } = await import('node:fs');
  writeFileSync(`${imagesDir}/og.png`, renderPng(readFileSync(`${imagesDir}/og.svg`), 1200));

  for (const dress of dresses) {
    const svg = drawing(dress, { sketch: false, backdrop: true });
    const pngPath = `/tmp/${dress.id}.png`;
    writeFileSync(pngPath, renderPng(svg, 560));
    const out = `${videosDir}/${dress.id}.mp4`;
    const result = spawnSync(
      'ffmpeg',
      [
        '-y',
        '-loop',
        '1',
        '-i',
        pngPath,
        '-vf',
        "scale=iw*0.78:ih*0.78,pad=iw/0.78:ih/0.78:(ow-iw)/2:(oh-ih)/2:0xFFFDF8,rotate=a='12*sin(2*PI*t/1.2)*PI/180':ow=iw:oh=ih:c=0xFFFDF8,scale=280:-2",
        '-t',
        '2.4',
        '-r',
        '12',
        '-an',
        '-c:v',
        'libx264',
        '-pix_fmt',
        'yuv420p',
        '-crf',
        '30',
        '-movflags',
        '+faststart',
        '-tune',
        'stillimage',
        out,
      ],
      { encoding: 'utf8' },
    );
    if (result.status !== 0) {
      console.error(result.stderr);
      process.exit(result.status ?? 1);
    }
    console.log('video', out);
  }
}
