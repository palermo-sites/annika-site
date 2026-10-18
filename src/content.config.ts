import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const designs = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/designs' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    date: z.coerce.date(),
    image: z.string(),
    imageAlt: z.string(),
    tags: z.array(z.string()).default([]),
  }),
});

const portfolio = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/portfolio' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    year: z.number(),
    silhouette: z.string(),
    fabrics: z.array(z.string()),
    details: z.array(z.string()),
    featured: z.boolean().default(false),
    order: z.number(),
    gallery: z.array(z.object({ src: z.string(), alt: z.string() })).min(1),
  }),
});

export const collections = { designs, portfolio };
