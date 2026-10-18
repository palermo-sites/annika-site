import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const figure = z.object({
  src: z.string(),
  alt: z.string(),
});

// One Markdown file in src/content/projects is one dress or collection.
// The home grid reads every file, so the count can change without a layout edit.
const projects = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/projects' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    // Free label, for example "Dress" or "Collection".
    kind: z.string().default('Dress'),
    year: z.number().optional(),
    // Pastel hex used on this project's tile and page.
    accent: z.string().regex(/^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/, 'accent must be a hex color'),
    order: z.number().default(0),
    placeholder: z.boolean().default(false),
    tags: z.array(z.string()).default([]),
    sketch: figure,
    // Still shown on the tile, and the fallback when a preview video cannot play.
    finished: figure,
    // Optional muted looping clip for the home-grid hover preview.
    preview: z.string().optional(),
    // What the project page places beside the sketch: images, video, or both.
    media: z
      .array(
        z.object({
          type: z.enum(['image', 'video']),
          src: z.string(),
          alt: z.string(),
          caption: z.string().optional(),
          poster: z.string().optional(),
        }),
      )
      .min(1),
  }),
});

export const collections = { projects };
