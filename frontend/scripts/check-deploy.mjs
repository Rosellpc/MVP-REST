import { readFileSync } from 'node:fs';

if (process.env.VERCEL) {
  const config = JSON.parse(readFileSync(new URL('../vercel.json', import.meta.url), 'utf8'));
  if (config.rewrites[0].destination.includes('.invalid')) {
    throw new Error('Configura la URL de Render con scripts/configure-deploy.mjs antes de desplegar.');
  }
}
