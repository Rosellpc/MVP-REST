import { readFileSync, writeFileSync } from 'node:fs';

const origin = new URL(process.argv[2] ?? 'https://invalid.local');
if (origin.protocol !== 'https:' || !origin.hostname.endsWith('.onrender.com') || origin.username || origin.password || origin.search || origin.hash || origin.pathname !== '/') {
  throw new Error('Uso: node scripts/configure-deploy.mjs https://TU-SERVICIO.onrender.com');
}
const file = new URL('../vercel.json', import.meta.url);
const config = JSON.parse(readFileSync(file, 'utf8'));
config.rewrites[0].destination = `${origin.origin}/api/:path*`;
writeFileSync(file, JSON.stringify(config, null, 2) + '\n');
console.log('Proxy de producción configurado. Revisa y guarda vercel.json en Git.');
