import { sites } from '@openai/sites-vite-plugin';
import tailwindcss from '@tailwindcss/postcss';
import vinext from 'vinext';
import { defineConfig } from 'vite';
export default defineConfig({
  plugins: [vinext(), sites()],
  css: { postcss: { plugins: [tailwindcss()] } },
  server: {
    watch: {
      // Blender and Windows image previews can lock these files while writing
      // or opening them. They are served on request and do not need code HMR.
      ignored: ['**/assets/**', '**/work/**', '**/public/models/**', '**/public/bakes/**', '**/public/renders/**', '**/optix7cache.db*'],
    },
  },
});
