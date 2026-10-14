// Deterministic frame renderer: drives the page in headless Chromium and pipes PNG frames to ffmpeg.
//
//   node render.mjs --scene s01_intro                 -> build/chunks/s01_intro.mp4
//   node render.mjs --scene s01_intro --stills 1,5,9  -> build/stills/s01_intro_<t>.png
//   options: --fps 30 --from 0 --to 12 --crf 16 --every N (render every Nth frame, for previews)
//            --video fatigue  (which video: selects timing/data in the page and build/<video>/ for output)
import { chromium } from 'playwright';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const args = Object.fromEntries(process.argv.slice(2).reduce((acc, a, i, arr) => {
  if (a.startsWith('--')) acc.push([a.slice(2), arr[i + 1] && !arr[i + 1].startsWith('--') ? arr[i + 1] : true]);
  return acc;
}, []));
const sceneId = args.scene;
const fps = Number(args.fps ?? 30);
const crf = Number(args.crf ?? 15);
const video = args.video ?? 'fea';
const BUILD = path.join(ROOT, 'build', ...(video === 'fea' ? [] : [video]));

const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json',
  '.css': 'text/css', '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf', '.png': 'image/png', '.jpg': 'image/jpeg' };

function serve() {
  return new Promise((resolve) => {
    const srv = http.createServer((req, res) => {
      const u = decodeURIComponent(req.url.split('?')[0]);
      const p = path.join(ROOT, u === '/' ? '/src/index.html' : u);
      if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
      res.writeHead(200, { 'Content-Type': MIME[path.extname(p)] ?? 'application/octet-stream', 'Cache-Control': 'no-cache' });
      fs.createReadStream(p).pipe(res);
    });
    srv.listen(0, '127.0.0.1', () => resolve(srv));
  });
}

const srv = await serve();
const port = srv.address().port;
const browser = await chromium.launch({
  // Mesa llvmpipe through ANGLE/EGL (surfaceless) is several times faster than SwiftShader here
  args: ['--use-gl=angle', '--use-angle=gl-egl', '--ignore-gpu-blocklist', '--disable-gpu-vsync',
    '--force-color-profile=srgb', '--font-render-hinting=none', '--disable-web-security'],
  env: { ...process.env, EGL_PLATFORM: 'surfaceless' },
});
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
const logs = [];
page.on('console', (m) => { const t = m.text(); logs.push(t); if (m.type() === 'error' || args.verbose) console.log('[page]', t); });
page.on('pageerror', (e) => console.log('[pageerror]', e.message));
await page.goto(`http://127.0.0.1:${port}/src/index.html?aa=${args.aa ?? 1}&video=${video}`);
const ok = await page.evaluate(() => window.__ready);
if (!ok) { console.log(await page.evaluate(() => window.__error)); process.exit(1); }
const meta = await page.evaluate(([id, o]) => window.__setup(id, o), [sceneId, { preview: !!args.preview, ...(args.opts ? JSON.parse(args.opts) : {}) }]);
fs.mkdirSync(path.join(BUILD, 'meta'), { recursive: true });
fs.writeFileSync(path.join(BUILD, 'meta', `${sceneId}.json`), JSON.stringify(meta, null, 1));
const cdp = await page.context().newCDPSession(page);
const grab = async () => Buffer.from((await cdp.send('Page.captureScreenshot', { format: 'png', optimizeForSpeed: true })).data, 'base64');

if (args.stills) {
  const dir = path.join(BUILD, 'stills');
  fs.mkdirSync(dir, { recursive: true });
  const ts = String(args.stills).split(',').map(Number);
  for (const t of ts) {
    const t0 = Date.now();
    await page.evaluate((tt) => window.__frame(tt), t);
    const buf = await grab();
    const f = path.join(dir, `${sceneId}_${t.toFixed(2)}.png`);
    fs.writeFileSync(f, buf);
    console.log('still', f, Date.now() - t0, 'ms');
  }
} else {
  const from = Number(args.from ?? 0);
  const to = Math.min(Number(args.to ?? meta.duration), meta.duration);
  const every = Number(args.every ?? 1);
  const n = Math.round((to - from) * fps);
  const dir = path.join(BUILD, 'chunks');
  fs.mkdirSync(dir, { recursive: true });
  const out = args.out ?? path.join(dir, `${sceneId}.mp4`);
  const outFps = fps / every;
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(outFps), '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', String(crf), '-pix_fmt', 'yuv420p', '-r', String(outFps), out],
  { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let i = 0; i < n; i += every) {
    const t = from + i / fps;
    await page.evaluate((tt) => window.__frame(tt), t);
    const buf = await grab();
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
    if (i % (fps * 5) < every) {
      const el = (Date.now() - t0) / 1000;
      console.log(`${sceneId}: t=${t.toFixed(1)}/${to.toFixed(1)}s  ${(el / (i / every + 1)).toFixed(3)} s/frame`);
    }
  }
  ff.stdin.end();
  await new Promise((r) => ff.on('close', r));
  console.log('wrote', out, 'in', ((Date.now() - t0) / 1000).toFixed(0), 's');
}
await browser.close();
srv.close();
