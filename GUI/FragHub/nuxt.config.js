// nuxt.config.js
export default defineNuxtConfig({
  ssr: false, // Important : rend l'application 100% côté client

  app: {
    baseURL: '/', // CRUCIAL : force les chemins d'assets à être relatifs
    buildAssetsDir: 'assets',
  },

  router: {
    options: {
      hashMode: true
    }
  },

  // 👇 LE CORRECTIF POUR ELECTRON EST ICI 👇
  experimental: {
    payloadExtraction: false, // Empêche Nuxt de fetcher _payload.json
    appManifest: false        // Empêche Nuxt de fetcher _builds/meta.json
  },

  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  modules: [
    'vuetify-nuxt-module'
  ],
  vuetify: {
    moduleOptions: {}
  }
})