import { existsSync } from 'node:fs';

if (process.env.VERCEL) {
  for (const file of ['../api/proxy.js', '../api/health.js']) {
    if (!existsSync(new URL(file, import.meta.url))) {
      throw new Error(`Missing required Vercel function: frontend/api/${file.slice(7)}`);
    }
  }
}
