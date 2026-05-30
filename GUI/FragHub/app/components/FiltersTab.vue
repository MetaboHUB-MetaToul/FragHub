<template>
  <v-container class="pa-2"> <v-card flat>
    <v-card-text class="pa-1"> <v-row v-for="filter in filters" :key="filter.id" align="center" no-gutters class="mb-1">

      <v-col cols="auto">
        <v-switch
            v-model="parameters[filter.id]"
            :true-value="1.0"
            :false-value="0.0"
            color="success"
            hide-details
            density="compact"
            inset
            class="scale-switch"
        ></v-switch>
      </v-col>

      <v-col cols="4">
        <div class="text-caption font-weight-bold">{{ filter.name }}</div>
      </v-col>

      <v-col cols="auto">
        <v-tooltip location="top">
          <template v-slot:activator="{ props }">
            <v-icon v-bind="props" color="grey" size="x-small">mdi-information-outline</v-icon>
          </template>
          <span class="text-caption">{{ filter.desc }}</span>
        </v-tooltip>
      </v-col>

      <v-col v-if="filter.params" class="d-flex justify-end">
        <div v-for="p in filter.params" :key="p.key" class="d-flex align-center ml-2">
          <span class="text-caption mr-1">{{ p.label }}</span>
          <v-text-field
              v-model.number="parameters[p.key]"
              type="number"
              variant="outlined"
              density="compact"
              hide-details
              style="width: 60px;"
              class="text-caption"
          ></v-text-field>
        </div>
      </v-col>
    </v-row>
    </v-card-text>
  </v-card>
  </v-container>
</template>

<style scoped>
/* Réduction visuelle du switch */
.scale-switch {
  transform: scale(0.85);
  transform-origin: left;
}
</style>

<script setup>
import { useState } from '#imports'

const parameters = useState('parameters')

// Définition de la structure des filtres
const filters = [
  { id: 'normalize_intensity', name: 'Normalize Intensity', desc: 'Normalizes intensity to max.' },
  { id: 'remove_peak_above_precursormz', name: 'Remove Above Precursor', desc: 'Removes peaks > precursor + 5 Da.' },
  { id: 'check_minimum_peak_requiered', name: 'Min Peaks Required', desc: 'Checks minimum number of peaks.', params: [{ label: 'N peaks:', key: 'check_minimum_peak_requiered_n_peaks' }] },
  { id: 'reduce_peak_list', name: 'Reduce Peak List', desc: 'Retains top intense peaks.', params: [{ label: 'Max:', key: 'reduce_peak_list_max_peaks' }] },
  { id: 'remove_spectrum_under_entropy_score', name: 'Entropy Score', desc: 'Filters by entropy score.', params: [{ label: 'Score:', key: 'remove_spectrum_under_entropy_score_value' }] },
  { id: 'keep_mz_in_range', name: 'Keep m/z Range', desc: 'Filters by m/z range.', params: [{ label: 'From:', key: 'keep_mz_in_range_from_mz' }, { label: 'To:', key: 'keep_mz_in_range_to_mz' }] },
  { id: 'check_minimum_of_high_peaks_requiered', name: 'High Peaks', desc: 'Min number of high intensity peaks.', params: [{ label: 'Int %:', key: 'check_minimum_of_high_peaks_requiered_intensity_percent' }, { label: 'N:', key: 'check_minimum_of_high_peaks_requiered_no_peaks' }] }
]
</script>