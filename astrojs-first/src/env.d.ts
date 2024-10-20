/// <reference path="../.astro/types.d.ts" />
/// <reference types="astro/client" />

interface Product {
  name: string;
  description: string;
  pubDate: Date;
  heroImage: string; 
}
interface AstroProduct {
  id: string;
  slug: string;
  body: string;
  collection: string;
  data: Product;
}
