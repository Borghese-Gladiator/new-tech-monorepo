// 1. Import utilities from `astro:content`
import { z, defineCollection } from 'astro:content';

// 2. Define a `type` and `schema` for each collection
const productCollection = defineCollection({
  type: 'content', // v2.5.0 and later
  schema: z.object({
		name: z.string(),
		description: z.string(),
		pubDate: z.coerce.date(),  // Transform string to Date object
		updatedDate: z.coerce.date().optional(),
		heroImage: z.string().optional(),
  }),
});

// 3. Export a single `collections` object to register your collection(s)
export const collections = {
  'product': productCollection,
};
