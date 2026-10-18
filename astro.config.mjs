// @ts-check
import { defineConfig } from 'astro/config';

// site is the final address. BASE_PATH is set by the deploy workflow while the site is served at
// https://palermo-sites.github.io/annika-site/; once annikapalermo.com points at Pages it is empty and the base is '/'.
export default defineConfig({
  site: 'https://annikapalermo.com',
  base: process.env.BASE_PATH || '/',
  output: 'static',
  outDir: './_site',
  trailingSlash: 'ignore',
});
