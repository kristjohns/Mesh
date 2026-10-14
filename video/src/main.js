import { Engine } from './engine/engine.js';
import { SCENES } from './scenes/index.js';

const engine = new Engine(document.getElementById('gl'), document.getElementById('c2d'), document.getElementById('dom'));
window.__engine = engine;
window.__ready = engine.init().then(() => true).catch((e) => { console.error(e); window.__error = String(e.stack || e); return false; });
window.__setup = async (id, opts) => {
  await window.__ready;
  if (!SCENES[id]) throw new Error('unknown scene ' + id);
  return engine.setup(SCENES[id], id, opts || {});
};
window.__frame = (t) => engine.frame(t);
