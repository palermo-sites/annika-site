// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// site is the final address: https://annikapalermo.com (UAT: https://uat.annikapalermo.com). Both are served at '/';
// BASE_PATH remains for a build served under a path.
export default defineConfig({
  site: 'https://annikapalermo.com',
  base: process.env.BASE_PATH || '/',
  output: 'static',
  outDir: './_site',
  trailingSlash: 'ignore',
  integrations: [sitemap()],
});
