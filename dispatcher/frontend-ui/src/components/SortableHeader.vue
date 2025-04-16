<template>
    <th @click="sort" :class="{ sortable: true, 'active-sort': isActive }">
      <slot></slot>
      <span v-if="isActive" class="sort-icon">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
    </th>
  </template>
  
  <script>
  export default {
    name: 'SortableHeader',
    props: {
      column: {
        type: String,
        required: true
      },
      currentSortColumn: {
        type: String,
        default: null
      },
      currentSortOrder: {
        type: String,
        default: null
      },
      sortable: {
        type: Boolean,
        default: true
      }
    },
    computed: {
      isActive() {
        return this.sortable && this.currentSortColumn === this.column;
      },
      sortOrder() {
        return this.currentSortOrder;
      }
    },
    methods: {
      sort() {
        if (!this.sortable) return;
        this.$emit('sort', this.column);
      }
    }
  }
  </script>
  
  <style scoped>
  .sortable {
    cursor: pointer;
    position: relative;
    user-select: none;
  }
  .sortable:hover {
    background-color: rgba(0, 0, 0, 0.05);
  }
  .sort-icon {
    margin-left: 5px;
    font-size: 0.8em;
  }
  </style>