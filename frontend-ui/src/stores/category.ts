import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useCategoryStore = defineStore('category', () => {
  const categories = ref<string[]>([
    "devdocs",
    "freecodecamp",
    "gutenberg",
    "ifixit",
    "other",
    "phet",
    "psiram",
    "stack_exchange",
    "ted",
    "openedx",
    "vikidia",
    "wikibooks",
    "wikihow",
    "wikinews",
    "wikipedia",
    "wikiquote",
    "wikisource",
    "wikispecies",
    "wikiversity",
    "wikivoyage",
    "wiktionary",
    "mindtouch",
  ])

  return {
    categories,
  }
})
