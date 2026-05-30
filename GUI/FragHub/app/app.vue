<template>
  <v-app>
    <v-main>
      <v-container class="fill-height position-relative pa-0" fluid>

        <div class="background-logo">
          <v-img
              src="~/assets/FragHub_icon.png"
              max-height="350"
              max-width="350"
              alt="FragHub Background Logo"
          ></v-img>
        </div>

        <v-card
            class="w-100 h-100 d-flex flex-column bg-transparent"
            elevation="0"
        >
          <div class="tabs-bandeau-wrapper">
            <v-tabs
                v-model="activeTab"
                class="tabs-bandeau"
                align-tabs="center"
                color="primary"
            >
              <v-tab value="input" class="modern-tab">INPUT</v-tab>
              <v-tab value="output" class="modern-tab">OUTPUT</v-tab>
              <v-tab value="filters" class="modern-tab">Filters</v-tab>
              <v-tab value="denovo" class="modern-tab">De Novo</v-tab>
              <v-tab value="output_settings" class="modern-tab">Output settings</v-tab>
              <v-tab value="projects" class="modern-tab">Projects settings</v-tab>
            </v-tabs>
          </div>

          <v-card-text class="flex-grow-1 overflow-y-auto pa-0 pb-16">
            <v-tabs-window v-model="activeTab" class="h-100">
              <v-tabs-window-item value="input" class="h-100"><InputTab /></v-tabs-window-item>
              <v-tabs-window-item value="output" class="h-100"><OutputTab /></v-tabs-window-item>
              <v-tabs-window-item value="filters" class="h-100"><FiltersTab /></v-tabs-window-item>
              <v-tabs-window-item value="denovo" class="h-100"><DeNovoTab /></v-tabs-window-item>
              <v-tabs-window-item value="output_settings" class="h-100"><OutputSettingTab /></v-tabs-window-item>
              <v-tabs-window-item value="projects" class="h-100"><ProjectsTab /></v-tabs-window-item>
            </v-tabs-window>
          </v-card-text>
        </v-card>

        <v-btn
            color="success"
            size="x-large"
            elevation="8"
            class="start-btn text-h6 font-weight-bold"
            @click="startExecution"
        >
          START
        </v-btn>

      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, useState } from '#imports'

const activeTab = ref('input')

const parameters = useState('parameters', () => ({
  input_directory: [],
  output_directory: "",
  calculate_de_novo: false,
  de_novo_ppm_tolerance: 10.0,
}))

const startExecution = async () => {
  console.log("Paramètres envoyés :", parameters.value)
}
</script>

<style scoped>
/* ========================================= */
/* STYLE DU BANDEAU MODERNE (Opaque)         */
/* ========================================= */
.tabs-bandeau-wrapper {
  width: 100%;
  background: #2b2b2b; /* Gris sombre totalement OPAQUE */
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3); /* Ombre un peu plus prononcée */
  z-index: 5;
}

.tabs-bandeau {
  background: transparent !important;
}

/* ========================================= */
/* STYLE DES ONGLETS & SÉPARATEURS           */
/* ========================================= */
.modern-tab {
  position: relative;
  color: #B0BEC5 !important;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.modern-tab.v-tab--selected {
  color: #2196F3 !important;
}

.modern-tab:not(:last-child)::after {
  content: '';
  position: absolute;
  right: 0;
  top: 35%;
  height: 30%;
  width: 2px;
  background-color: rgba(255, 255, 255, 0.15);
  border-radius: 2px;
}

/* ========================================= */
/* LOGO FILIGRANE & BOUTON FLOTTANT          */
/* ========================================= */
.background-logo {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 0;
  pointer-events: none;
  opacity: 0.25; /* PASSÉ DE 0.08 à 0.25 pour bien le faire ressortir ! */
  width: 100%;
  display: flex;
  justify-content: center;
}

.start-btn {
  position: absolute;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  min-width: 250px;
  border-radius: 30px;
}
</style>