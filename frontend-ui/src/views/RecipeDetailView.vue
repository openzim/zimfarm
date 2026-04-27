<!-- Recipe detail view
  - listing all info
  - fire recipe button -->

<template>
  <v-container>
    <!-- Action Button Row -->
    <v-row v-if="recipe">
      <v-col>
        <RecipeActionButton
          :enabled="recipe.enabled && !recipe.archived"
          :ready="ready"
          :task="task"
          :requested-task="requestedTask"
          :workers="workers"
          :working-text="workingText"
          @request-task="requestTask"
          @fire-existing-task="fireExistingTask"
          @cancel-task="cancelTask"
          @unrequest-task="unrequestTask"
        />
      </v-col>
    </v-row>

    <!-- Title Row -->
    <v-row>
      <v-col>
        <h2 class="text-h6 text-md-h4">
          <code>{{ recipeName }}</code>
        </h2>
      </v-col>
    </v-row>

    <!-- Loading State -->
    <div v-if="!ready && !error" class="text-center pa-8">
      <v-progress-circular indeterminate size="64" color="primary" />
      <div class="mt-4 text-body-1">Loading recipe data...</div>
    </div>

    <!-- Content -->
    <div v-if="ready && recipe">
      <!-- Tabs -->
      <v-tabs
        v-model="currentTab"
        class="mb-4"
        color="primary"
        slider-color="primary"
        :grow="!smAndDown"
        show-arrows
      >
        <v-tab
          base-color="primary"
          value="details"
          :to="{
            name: 'recipe-detail',
            params: { recipeName: recipeName },
          }"
        >
          <v-icon class="mr-2">mdi-information</v-icon>
          Info
        </v-tab>
        <v-tab
          base-color="primary"
          value="config"
          :to="{
            name: 'recipe-detail-tab',
            params: { recipeName: recipeName, selectedTab: 'config' },
          }"
        >
          <v-icon class="mr-2">mdi-cog</v-icon>
          Config
        </v-tab>
        <v-tab
          base-color="primary"
          v-if="canUpdateRecipes"
          value="history"
          :to="{
            name: 'recipe-detail-tab',
            params: { recipeName: recipeName, selectedTab: 'history' },
          }"
        >
          <v-icon class="mr-2">mdi-history</v-icon>
          History
        </v-tab>
        <v-tab
          base-color="primary"
          v-if="canUpdateRecipes && !recipe?.archived"
          value="edit"
          :to="{
            name: 'recipe-detail-tab',
            params: { recipeName: recipeName, selectedTab: 'edit' },
          }"
        >
          <v-icon class="mr-2">mdi-pencil</v-icon>
          Edit
        </v-tab>
        <v-tab
          base-color="primary"
          v-if="canCreateRecipes && !recipe?.archived"
          value="clone"
          :to="{
            name: 'recipe-detail-tab',
            params: { recipeName: recipeName, selectedTab: 'clone' },
          }"
        >
          <v-icon class="mr-2">mdi-content-copy</v-icon>
          Clone
        </v-tab>
        <v-tab
          base-color="primary"
          v-if="canArchiveRecipes"
          value="archive"
          :to="{
            name: 'recipe-detail-tab',
            params: { recipeName: recipeName, selectedTab: 'archive' },
          }"
        >
          <v-icon class="mr-2">{{
            recipe?.archived ? 'mdi-archive-arrow-up' : 'mdi-archive'
          }}</v-icon>
          {{ recipe?.archived ? 'Restore' : 'Archive' }}
        </v-tab>

        <v-tab
          base-color="primary"
          value="similar"
          :to="{
            name: 'recipe-detail-tab',
            params: { recipeName: recipeName, selectedTab: 'similar' },
          }"
        >
          <v-icon class="mr-2">mdi-creation</v-icon>
          Similar
        </v-tab>

        <v-tab
          base-color="error"
          v-if="canDeleteRecipes && recipe?.archived"
          value="delete"
          :to="{
            name: 'recipe-detail-tab',
            params: { recipeName: recipeName, selectedTab: 'delete' },
          }"
        >
          <v-icon class="mr-2">mdi-delete</v-icon>
          Delete
        </v-tab>
      </v-tabs>

      <!-- Tab Content -->
      <v-window v-model="currentTab">
        <!-- Details Tab -->
        <v-window-item value="details">
          <v-card flat>
            <v-card-text class="pa-0">
              <div class="ml-4 mr-4 mt-2 mb-2">
                <v-row no-gutters class="py-2">
                  <v-col cols="12" md="4">
                    <div class="text-subtitle-2">API</div>
                  </v-col>
                  <v-col cols="12" md="8">
                    <a
                      target="_blank"
                      :href="webApiUrl + '/recipes/' + recipeName"
                      class="text-decoration-none"
                    >
                      document
                      <v-icon size="small" class="ml-1">mdi-open-in-new</v-icon>
                    </a>
                  </v-col>
                </v-row>
                <v-divider class="my-2"></v-divider>

                <v-row no-gutters class="py-2">
                  <v-col cols="12" md="4">
                    <div class="text-subtitle-2">Category</div>
                  </v-col>
                  <v-col cols="12" md="8">{{ recipe.category }}</v-col>
                </v-row>
                <v-divider class="my-2"></v-divider>

                <v-row no-gutters class="py-2">
                  <v-col cols="12" md="4">
                    <div class="text-subtitle-2">Language</div>
                  </v-col>
                  <v-col cols="12" md="8">
                    {{ recipe.language.name }}
                    (<code>{{ recipe.language.code }}</code
                    >)
                  </v-col>
                </v-row>
                <v-divider class="my-2"></v-divider>

                <v-row no-gutters class="py-2">
                  <v-col cols="12" md="4">
                    <div class="text-subtitle-2">Enabled</div>
                  </v-col>
                  <v-col cols="12" md="8">
                    <v-chip
                      :color="recipe?.enabled ? 'success' : 'error'"
                      size="small"
                      variant="tonal"
                    >
                      {{ recipe?.enabled }}
                    </v-chip>
                  </v-col>
                </v-row>
                <v-divider class="my-2"></v-divider>

                <v-row no-gutters class="py-2">
                  <v-col cols="12" md="4">
                    <div class="text-subtitle-2">Archived</div>
                  </v-col>
                  <v-col cols="12" md="8">{{ recipe?.archived ? 'Yes' : 'No' }}</v-col>
                </v-row>
                <v-divider class="my-2"></v-divider>

                <v-row no-gutters class="py-2">
                  <v-col cols="12" md="4">
                    <div class="text-subtitle-2">Periodicity</div>
                  </v-col>
                  <v-col cols="12" md="8">
                    <code>{{ recipe?.periodicity }}</code>
                  </v-col>
                </v-row>
                <v-divider class="my-2"></v-divider>

                <v-row v-if="recipe?.tags?.length" no-gutters class="py-2">
                  <v-col cols="12" md="4">
                    <div class="text-subtitle-2">Tags</div>
                  </v-col>
                  <v-col cols="12" md="8">
                    <div class="d-flex flex-row flex-wrap">
                      <v-chip
                        v-for="tag in recipe?.tags || []"
                        :key="tag"
                        size="small"
                        color="primary"
                        variant="outlined"
                        density="comfortable"
                        class="mr-2 mb-1 text-caption text-uppercase"
                      >
                        {{ tag }}
                      </v-chip>
                    </div>
                  </v-col>
                </v-row>
                <v-divider v-if="recipe?.tags?.length" class="my-2"></v-divider>

                <v-row no-gutters class="py-2">
                  <v-col cols="12" md="4">
                    <div class="text-subtitle-2">Context</div>
                  </v-col>
                  <v-col cols="12" md="8">
                    <v-chip
                      v-if="recipe.context"
                      size="small"
                      variant="outlined"
                      density="comfortable"
                      color="primary"
                      class="mr-2 mb-1 text-caption text-uppercase"
                    >
                      {{ recipe.context }}
                    </v-chip>
                  </v-col>
                </v-row>
                <v-divider class="my-2"></v-divider>

                <v-row no-gutters class="py-2">
                  <v-col cols="12" md="4">
                    <div class="text-subtitle-2">Last run</div>
                  </v-col>
                  <v-col cols="12" md="8">
                    <StatusDisplay
                      v-if="lastRun"
                      :status="lastRun.status"
                      :timestamp="lastRun.timestamp"
                      :updated-at="lastRun.updated_at"
                      :task-id="lastRun.id"
                      :justify-on-small="false"
                    />
                    <div v-else>
                      <v-chip size="small" variant="outlined" color="grey"> None 🙁 </v-chip>
                    </div>
                  </v-col>
                </v-row>
                <v-divider class="my-2"></v-divider>

                <v-row v-if="recipeDurationDict" no-gutters class="py-2">
                  <v-col cols="12" md="4">
                    <div class="text-subtitle-2">Scraper Duration</div>
                  </v-col>
                  <v-col cols="12" md="8">
                    <span v-if="recipeDurationDict.single">
                      {{ recipeDurationDict.formattedDuration }}
                      (<router-link
                        :to="{
                          name: 'worker-detail',
                          params: { workerName: recipeDurationDict.worker },
                        }"
                      >
                        {{ recipeDurationDict.worker }}
                      </router-link>
                      on
                      {{ formatDt(recipeDurationDict.on) }})
                    </span>
                    <span v-else>
                      between
                      {{ recipeDurationDict.formattedMinDuration }}
                      (<template
                        v-for="(worker, index) in recipeDurationDict.minWorkers || []"
                        :key="worker.worker_name"
                      >
                        <router-link
                          :to="{
                            name: 'worker-detail',
                            params: { workerName: worker.worker_name },
                          }"
                        >
                          {{ worker.worker_name }} </router-link
                        ><span v-if="index < (recipeDurationDict.minWorkers?.length || 0) - 1"
                          >,
                        </span> </template
                      >) and
                      {{ recipeDurationDict.formattedMaxDuration }}
                      (<template
                        v-for="(worker, index) in recipeDurationDict.maxWorkers || []"
                        :key="worker.worker_name"
                      >
                        <router-link
                          :to="{
                            name: 'worker-detail',
                            params: { workerName: worker.worker_name },
                          }"
                        >
                          {{ worker.worker_name }} </router-link
                        ><span v-if="index < (recipeDurationDict.maxWorkers?.length || 0) - 1"
                          >,
                        </span> </template
                      >)
                    </span>
                  </v-col>
                </v-row>
                <v-divider v-if="recipeDurationDict" class="my-2"></v-divider>

                <v-row v-if="totalDurationDict" no-gutters class="py-2">
                  <v-col cols="12" md="4">
                    <div class="text-subtitle-2">Total Duration</div>
                  </v-col>
                  <v-col cols="12" md="8">
                    <span v-if="totalDurationDict.single">
                      {{ totalDurationDict.formattedDuration }}
                      (<router-link
                        :to="{
                          name: 'worker-detail',
                          params: { workerName: totalDurationDict.worker },
                        }"
                      >
                        {{ totalDurationDict.worker }}
                      </router-link>
                      on
                      {{ formatDt(totalDurationDict.on) }})
                    </span>
                    <span v-else>
                      between
                      {{ totalDurationDict.formattedMinDuration }}
                      (<template
                        v-for="(worker, index) in totalDurationDict.minWorkers || []"
                        :key="worker.worker_name"
                      >
                        <router-link
                          :to="{
                            name: 'worker-detail',
                            params: { workerName: worker.worker_name },
                          }"
                        >
                          {{ worker.worker_name }} </router-link
                        ><span v-if="index < (totalDurationDict.minWorkers?.length || 0) - 1"
                          >,
                        </span> </template
                      >) and
                      {{ totalDurationDict.formattedMaxDuration }}
                      (<template
                        v-for="(worker, index) in totalDurationDict.maxWorkers || []"
                        :key="worker.worker_name"
                      >
                        <router-link
                          :to="{
                            name: 'worker-detail',
                            params: { workerName: worker.worker_name },
                          }"
                        >
                          {{ worker.worker_name }} </router-link
                        ><span v-if="index < (totalDurationDict.maxWorkers?.length || 0) - 1"
                          >,
                        </span> </template
                      >)
                    </span>
                  </v-col>
                </v-row>
                <v-divider v-if="totalDurationDict" class="my-2"></v-divider>

                <v-row v-if="!canRequestTasks" no-gutters class="py-2">
                  <v-col cols="12" md="4">
                    <div class="text-subtitle-2">Requested</div>
                  </v-col>
                  <v-col cols="12" md="8">
                    <div v-if="loadingRequestedTask">
                      <v-progress-circular indeterminate size="16" />
                    </div>
                    <div v-else-if="requestedTask">
                      <code>{{ shortId(requestedTask.id) }}</code
                      >,
                      {{
                        fromNow(getTimestampStringForStatus(requestedTask.timestamp, 'requested'))
                      }}
                      <v-chip
                        v-if="requestedTask.priority"
                        size="small"
                        color="warning"
                        variant="tonal"
                        class="ml-2"
                      >
                        <v-icon size="small" class="mr-1">mdi-fire</v-icon>
                        {{ requestedTask.priority }}
                      </v-chip>
                    </div>
                    <div v-else>No</div>
                  </v-col>
                </v-row>
                <v-divider v-if="!canRequestTasks" class="my-2"></v-divider>

                <div>
                  <v-row no-gutters class="py-2">
                    <v-col cols="12" md="4">
                      <div class="text-subtitle-2">History</div>
                    </v-col>
                    <v-col cols="12" md="8">
                      <div class="text-grey-darken-1"></div>
                    </v-col>
                  </v-row>
                  <div>
                    <v-data-table
                      :items="historyRuns"
                      :headers="[
                        { title: 'Worker', value: 'worker' },
                        { title: 'Status', value: 'status' },
                        { title: 'Total Duration', value: 'total_duration' },
                      ]"
                      :mobile="smAndDown"
                      :density="smAndDown ? 'compact' : 'comfortable'"
                      item-key="id"
                      :hide-default-footer="true"
                      disable-sort
                    >
                      <template #no-data>
                        <div class="text-center pa-4">
                          <v-icon size="x-large" class="mb-2">mdi-format-list-bulleted</v-icon>
                          <div class="text-h6 text-grey-darken-1 mb-2">No history</div>
                        </div>
                      </template>

                      <template #[`item.worker`]="{ item }">
                        <router-link
                          :to="{ name: 'worker-detail', params: { workerName: item.worker_name } }"
                          class="text-decoration-none"
                        >
                          {{ item.worker_name }}
                        </router-link>
                      </template>

                      <template #[`item.status`]="{ item }">
                        <StatusDisplay
                          :status="item.status"
                          :timestamp="item.timestamp"
                          :updated-at="item.updated_at"
                          :task-id="item.id"
                        />
                      </template>

                      <template #[`item.total_duration`]="{ item }">
                        <span>{{ calculateTaskDuration(item) }}</span>
                      </template>
                    </v-data-table>
                  </div>
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-window-item>

        <!-- History Tab -->
        <v-window-item value="history">
          <RecipeHistory
            v-if="canUpdateRecipes"
            :history="recipeHistoryStore.history"
            :has-more="canLoadMoreHistory"
            :loading="loadingHistory"
            :paginator="recipeHistoryStore.paginator"
            :recipe-name="recipeName"
            @load="loadHistory"
            @revert="handleRevert"
          />
        </v-window-item>

        <!-- Config Tab -->
        <v-window-item value="config">
          <v-card flat>
            <v-card-text class="pa-0">
              <div class="ml-4 mr-4 mt-2 mb-2">
                <v-row no-gutters class="py-2">
                  <v-col cols="12" md="4">
                    <div class="text-subtitle-2">Offliner</div>
                  </v-col>
                  <v-col cols="12" md="8">
                    <code>{{ offliner }}</code>
                  </v-col>
                </v-row>
                <v-divider class="my-2"></v-divider>

                <v-row no-gutters class="py-2">
                  <v-col cols="12" md="4">
                    <div class="text-subtitle-2">Offliner Definition</div>
                  </v-col>
                  <v-col cols="12" md="8">
                    <code>{{ recipe.version }}</code>
                  </v-col>
                </v-row>
                <v-divider class="my-2"></v-divider>

                <v-row no-gutters class="py-2">
                  <v-col cols="12" md="4">
                    <div class="text-subtitle-2">Platform</div>
                  </v-col>
                  <v-col cols="12" md="8">
                    <code>{{ platform || '-' }}</code>
                  </v-col>
                </v-row>
                <v-divider class="my-2"></v-divider>

                <v-row no-gutters class="py-2" v-if="!appConfig.DISABLE_WAREHOUSE_PATH">
                  <v-col cols="12" md="4">
                    <div class="text-subtitle-2">Warehouse Path</div>
                  </v-col>
                  <v-col cols="12" md="8">
                    <code>{{ warehousePath }}</code>
                  </v-col>
                </v-row>
                <v-divider class="my-2" v-if="!appConfig.DISABLE_WAREHOUSE_PATH"></v-divider>

                <v-row no-gutters class="py-2">
                  <v-col cols="12" md="4">
                    <div class="text-subtitle-2">Image</div>
                  </v-col>
                  <v-col cols="12" md="8">
                    <a target="_blank" :href="imageUrl" class="text-decoration-none">
                      <code>{{ imageHuman }}</code>
                    </a>
                  </v-col>
                </v-row>
                <v-divider class="my-2"></v-divider>

                <v-row no-gutters class="py-2">
                  <v-col cols="12" md="4">
                    <div class="text-subtitle-2">Resources</div>
                  </v-col>
                  <v-col cols="12" md="8">
                    <div class="d-flex flex-row flex-wrap ga-1">
                      <ResourceBadge kind="cpu" :value="config.resources.cpu" />
                      <ResourceBadge kind="memory" :value="config.resources.memory" />
                      <ResourceBadge kind="disk" :value="config.resources.disk" />
                      <ResourceBadge
                        kind="shm"
                        :value="config.resources.shm"
                        v-if="config.resources.shm"
                      />
                      <v-chip
                        v-if="config.monitor || false"
                        size="small"
                        color="warning"
                        variant="tonal"
                        class="ml-2"
                      >
                        <v-icon size="small" class="mr-1">mdi-bug</v-icon>
                        monitored
                      </v-chip>
                    </div>
                  </v-col>
                </v-row>
                <v-divider class="my-2"></v-divider>

                <v-row v-if="recipe?.config?.artifacts_globs" no-gutters class="py-2">
                  <v-col cols="12" md="4">
                    <div class="text-subtitle-2">Artifacts</div>
                  </v-col>
                  <v-col cols="12" md="8">
                    <code class="text-pink-accent-2">{{ recipe?.config?.artifacts_globs }}</code>
                  </v-col>
                </v-row>
                <v-divider v-if="recipe?.config?.artifacts_globs" class="my-2"></v-divider>

                <v-row no-gutters class="py-2">
                  <v-col cols="12" md="4">
                    <div class="text-subtitle-2">Config</div>
                  </v-col>
                  <v-col cols="12" md="8" class="text-break">
                    <FlagsList :offliner="config.offliner" :flags-definition="flagsDefinition" />
                  </v-col>
                </v-row>
                <v-divider class="my-2"></v-divider>

                <v-row no-gutters class="py-2">
                  <v-col cols="12" md="4">
                    <div class="text-subtitle-2">
                      Command
                      <v-btn
                        size="small"
                        variant="outlined"
                        class="ml-2"
                        @click="copyCommand(command)"
                      >
                        <v-icon size="small" class="mr-1">mdi-content-copy</v-icon>
                        Copy
                      </v-btn>
                    </div>
                  </v-col>
                  <v-col cols="12" md="8" class="text-break">
                    <code class="text-pink-accent-2">{{ command }}</code>
                  </v-col>
                </v-row>
                <v-divider class="my-2"></v-divider>

                <v-row no-gutters class="py-2">
                  <v-col cols="12" md="4">
                    <div class="text-subtitle-2">
                      Offliner Command
                      <v-btn
                        size="small"
                        variant="outlined"
                        class="ml-2"
                        @click="copyCommand(offlinerCommand)"
                      >
                        <v-icon size="small" class="mr-1">mdi-content-copy</v-icon>
                        Copy
                      </v-btn>
                    </div>
                  </v-col>
                  <v-col cols="12" md="8" class="text-break">
                    <code class="text-pink-accent-2">{{ offlinerCommand }}</code>
                  </v-col>
                </v-row>
              </div>
            </v-card-text>
          </v-card>
        </v-window-item>

        <!-- Edit Tab -->
        <v-window-item value="edit">
          <div v-if="canUpdateRecipes" class="pa-4">
            <!-- Validation Status -->
            <v-alert
              v-if="recipe"
              :type="recipe.is_valid ? 'success' : 'error'"
              variant="tonal"
              class="mb-4"
              closable
            >
              <template #prepend>
                <v-icon :icon="recipe.is_valid ? 'mdi-check-circle' : 'mdi-alert-circle'" />
              </template>
              <strong>{{
                recipe.is_valid ? 'Recipe is valid' : 'Recipe has validation errors'
              }}</strong>
              <div v-if="!recipe.is_valid" class="mt-2">
                Please fix the configuration issues below.
              </div>
            </v-alert>

            <RecipeEditor
              :recipe="recipe"
              :offliners="offliners"
              :platforms="platforms"
              :languages="languages"
              :tags="tags"
              :contexts="contexts"
              :flags-definition="flagsDefinition"
              :help-url="helpUrl"
              :offliner-versions="offlinerVersions"
              :image-tags="imageTags"
              @submit="updateRecipe"
              @image-name-change="fetchRecipeImageTags"
              @offliner-change="handleOfflinerChange"
              @offliner-version-change="handleOfflinerVersionChange"
            />
          </div>
        </v-window-item>

        <!-- Clone Tab -->
        <v-window-item value="clone">
          <div v-if="canCreateRecipes" class="pa-4">
            <CloneRecipe :from="recipeName" @clone="cloneRecipe" />
          </div>
        </v-window-item>

        <!-- Archive Tab -->
        <v-window-item value="archive">
          <div v-if="canArchiveRecipes" class="pa-4">
            <ArchiveItem
              :name="recipeName"
              :is-archived="recipe?.archived || false"
              @archive-item="archiveRecipe"
              @restore-item="restoreRecipe"
            />
          </div>
        </v-window-item>

        <!-- Delete Tab -->
        <v-window-item value="delete">
          <div v-if="canDeleteRecipes" class="pa-4">
            <DeleteItem
              :name="recipeName"
              description="recipe"
              property="name"
              @delete-item="deleteRecipe"
            />
          </div>
        </v-window-item>

        <!-- Similar Tab -->
        <v-window-item value="similar">
          <v-card flat>
            <v-card-text>
              <div class="mb-4 text-body-1">
                Recipes similar to <code>{{ recipeName }}</code>
              </div>
              <RecipesTable
                :headers="similarHeaders"
                :recipes="recipes"
                :paginator="recipeStore.paginator"
                :loading="loadingSimilar"
                :errors="recipeStore.errors"
                :loading-text="'Fetching similar recipes...'"
                :show-selection="false"
                :show-filters="false"
                @load-data="loadSimilar"
                @limit-changed="handleLimitChange"
              />
            </v-card-text>
          </v-card>
        </v-window-item>
      </v-window>
    </div>

    <ErrorMessage v-if="error" :message="error" />
  </v-container>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import ArchiveItem from '@/components/ArchiveItem.vue'
import CloneRecipe from '@/components/CloneRecipe.vue'
import DeleteItem from '@/components/DeleteItem.vue'
import ErrorMessage from '@/components/ErrorMessage.vue'
import FlagsList from '@/components/FlagsList.vue'
import ResourceBadge from '@/components/ResourceBadge.vue'
import RecipeActionButton from '@/components/RecipeActionButton.vue'
import RecipeEditor from '@/components/RecipeEditor.vue'
import RecipeHistory from '@/components/RecipeHistory.vue'
import RecipesTable from '@/components/RecipesTable.vue'
import StatusDisplay from '@/components/StatusDisplay.vue'
import type { Config } from '@/config'
import constants from '@/constants'
import { useAuthStore } from '@/stores/auth'
import { useContextStore } from '@/stores/context'
import { useLanguageStore } from '@/stores/language'
import { useNotificationStore } from '@/stores/notification'
import { useOfflinerStore } from '@/stores/offliner'
import { usePlatformStore } from '@/stores/platform'
import { useRequestedTasksStore } from '@/stores/requestedTasks'
import { useRecipeStore } from '@/stores/recipe'
import { useRecipeHistoryStore } from '@/stores/recipeHistory'
import { useTagStore } from '@/stores/tag'
import { useTasksStore } from '@/stores/tasks'
import { useWorkersStore } from '@/stores/workers'
import type { Language } from '@/types/language'
import type { OfflinerDefinition } from '@/types/offliner'
import type { RequestedTaskLight } from '@/types/requestedTasks'
import type { ExpandedRecipeConfig, Recipe, RecipeLight, RecipeUpdateSchema } from '@/types/recipe'
import type { TaskLight } from '@/types/tasks'
import type { Worker } from '@/types/workers'
import { formatDt, formatDurationBetween, fromNow } from '@/utils/format'
import {
  buildCommandWithout,
  buildDockerCommand,
  buildRecipeDuration,
  buildTotalDurationDict,
  imageHuman as imageHumanFn,
  imageUrl as imageUrlFn,
} from '@/utils/offliner'
import { getTimestampStringForStatus } from '@/utils/timestamp'
import { inject } from 'vue'
import { useDisplay } from 'vuetify'

// Props
interface Props {
  recipeName: string
  selectedTab?: string
}

const props = withDefaults(defineProps<Props>(), {
  selectedTab: 'details',
})

// Router and stores
const router = useRouter()

const authStore = useAuthStore()
const notificationStore = useNotificationStore()
const recipeStore = useRecipeStore()
const recipeHistoryStore = useRecipeHistoryStore()
const requestedTasksStore = useRequestedTasksStore()
const tasksStore = useTasksStore()
const workersStore = useWorkersStore()
const tagStore = useTagStore()
const contextStore = useContextStore()
const languageStore = useLanguageStore()
const offlinerStore = useOfflinerStore()
const platformStore = usePlatformStore()

// Config
const appConfig = inject<Config>(constants.config)
if (!appConfig) {
  throw new Error('Config is not defined')
}

const { smAndDown } = useDisplay()

// Reactive data

const error = ref<string | null>(null)
const workingText = ref<string | null>(null)
const imageTags = ref<string[]>([])
const tags = ref<string[]>([])
const contexts = ref<string[]>([])
const languages = ref<Language[]>([])
const offliners = ref<string[]>([])
const offlinerVersions = ref<string[]>([])
const platforms = ref<string[]>([])
const flagsDefinition = ref<OfflinerDefinition[]>([])
const helpUrl = ref<string>('')

const ready = ref<boolean>(false)
const recipe = ref<Recipe | null>(null)
const loadingHistory = ref<boolean>(false)
const loadingRequestedTask = ref<boolean>(false)
// existing requested task for this recipe
const requestedTask = ref<RequestedTaskLight | null>(null)
// existing running task for this recipe
const task = ref<TaskLight | null>(null)
// history of runs for this recipe
const historyRuns = ref<TaskLight[]>([])
// current tab
const currentTab = ref(props.selectedTab)
// active workers
const workers = ref<Worker[]>([])

// Similar recipes state
const recipes = ref<RecipeLight[]>([])
const loadingSimilar = ref(false)
const similarHeaders = [
  { title: 'Name', value: 'name' },
  { title: 'Category', value: 'category' },
  { title: 'Language', value: 'language' },
  { title: 'Offliner', value: 'offliner' },
]

// Computed properties
const webApiUrl = computed(() => appConfig.ZIMFARM_WEBAPI)
const lastRun = computed(() => recipe.value?.most_recent_task || null)
const config = computed(() => recipe.value?.config || ({} as ExpandedRecipeConfig))
const offliner = computed(() => config.value?.offliner?.offliner_id || '')
const platform = computed(() => config.value?.platform || '')
const warehousePath = computed(() => config.value?.warehouse_path || '')
const imageHuman = computed(() => imageHumanFn(config.value))
const imageUrl = computed(() => imageUrlFn(config.value))
const command = computed(() => buildDockerCommand(recipe.value?.name || '', config.value))
const offlinerCommand = computed(() => buildCommandWithout(config.value))
const recipeDurationDict = computed(() => {
  return buildRecipeDuration(recipe.value?.duration || null)
})
const totalDurationDict = computed(() => {
  return buildTotalDurationDict(historyRuns.value)
})

// Permission computed properties
const canRequestTasks = computed(() => authStore.hasPermission('requested_tasks', 'create'))
const canUpdateRecipes = computed(() => authStore.hasPermission('recipes', 'update'))
const canCreateRecipes = computed(() => authStore.hasPermission('recipes', 'create'))
const canArchiveRecipes = computed(() => authStore.hasPermission('recipes', 'archive'))
const canDeleteRecipes = computed(() => authStore.hasPermission('recipes', 'delete'))

// History-related computed properties
const canLoadMoreHistory = computed(() => {
  const { skip, limit, count } = recipeHistoryStore.paginator
  return skip + limit < count
})

const loadSimilar = async (limit: number, skip: number) => {
  if (!recipe.value) return
  loadingSimilar.value = true
  const response = await recipeStore.fetchSimilarRecipes(recipe.value.name, {
    limit,
    skip,
    archived: false,
  })
  if (response) {
    recipes.value = response.items
    recipeStore.paginator = response.meta
  } else {
    recipes.value = []
    for (const error of recipeStore.errors) {
      notificationStore.showError(error)
    }
  }
  loadingSimilar.value = false
}

async function handleLimitChange(newLimit: number) {
  recipeStore.savePaginatorLimit(newLimit)
}

// Methods
const fetchWorkers = async () => {
  const response = await workersStore.fetchWorkers()
  if (response) {
    workers.value = response
  } else {
    for (const error of workersStore.errors) {
      notificationStore.showError(error)
    }
    workers.value = []
  }
}

const fetchRecipeTasks = async (onSuccess?: () => void) => {
  // Reset state
  loadingRequestedTask.value = true
  requestedTask.value = null
  task.value = null

  // Fetch requested tasks
  const response = await requestedTasksStore.fetchRequestedTasks({
    recipeName: [props.recipeName],
  })
  if (response) {
    loadingRequestedTask.value = false
    if (response.length > 0) {
      requestedTask.value = response[0]
    }
    // fetch history runs
    const historyRunsResponse = await tasksStore.fetchTasks({
      recipeName: props.recipeName,
    })
    if (historyRunsResponse) {
      historyRuns.value = historyRunsResponse
    } else {
      for (const error of tasksStore.errors) {
        notificationStore.showError(error)
      }
    }

    // fetch running tasks
    const tasksResponse = await tasksStore.fetchTasks({
      recipeName: props.recipeName,
      status: constants.CANCELABLE_STATUSES,
    })
    if (tasksResponse) {
      if (tasksResponse.length > 0) {
        task.value = tasksResponse[0]
      }
      // now that we have received all the data, we can call the onSuccess callback
      onSuccess?.()
    } else {
      if (tasksStore.errors.length > 0) {
        for (const error of tasksStore.errors) {
          notificationStore.showError(error)
        }
      }
    }
  } else {
    loadingRequestedTask.value = false
    if (requestedTasksStore.errors.length > 0) {
      for (const error of requestedTasksStore.errors) {
        notificationStore.showError(error)
      }
    }
  }
}

const copyCommand = async (command: string) => {
  try {
    await navigator.clipboard.writeText(command)
    notificationStore.showSuccess('Command copied to clipboard!')
  } catch {
    notificationStore.showWarning(
      'Unable to copy command to clipboard 😞. Please copy it manually.',
    )
  }
}

const requestTask = async (workerName: string | null, priority?: boolean) => {
  workingText.value = 'Requesting task…'

  const body: {
    recipeNames: string[]
    worker: string | null
    priority: number | null
  } = {
    recipeNames: [props.recipeName],
    worker: workerName,
    priority: priority ? constants.DEFAULT_FIRE_PRIORITY : null,
  }

  const response = await requestedTasksStore.requestTasks(body)
  if (response) {
    const msg = `Recipe <em>${props.recipeName}</em> has been requested as <code>${shortId(
      response.requested[0],
    )}</code>.`
    notificationStore.showSuccess(msg)
    workingText.value = null
    // update the requested task
    if (requestedTask.value) {
      requestedTask.value.id = response.requested[0]
      requestedTask.value.priority = priority ? constants.DEFAULT_FIRE_PRIORITY : 0
    }
    await fetchRecipeTasks()
  } else {
    for (const error of requestedTasksStore.errors) {
      notificationStore.showError(error)
    }
  }
  workingText.value = null
}

const fireExistingTask = async () => {
  if (!requestedTask.value) return

  workingText.value = 'Firing it up…'

  const response = await requestedTasksStore.updateRequestedTask(requestedTask.value.id, {
    priority: constants.DEFAULT_FIRE_PRIORITY,
  })
  if (response) {
    const msg = `Added priority to request <code>${shortId(requestedTask.value.id)}</code>.`
    notificationStore.showSuccess(msg)
  } else {
    for (const error of requestedTasksStore.errors) {
      notificationStore.showError(error)
    }
  }
  workingText.value = null
}

const cancelTask = async () => {
  if (!task.value) return

  workingText.value = 'Canceling task…'

  const response = await tasksStore.cancelTask(task.value.id)
  if (response) {
    const msg = `Requested Task <code>${shortId(task.value.id)}</code> has been marked for cancellation.`
    notificationStore.showSuccess(msg)
    task.value = null
    await fetchRecipeTasks()
  } else {
    for (const error of tasksStore.errors) {
      notificationStore.showError(error)
    }
  }
  workingText.value = null
}

const unrequestTask = async () => {
  if (!requestedTask.value) return

  workingText.value = 'Un-requesting task…'

  const response = await requestedTasksStore.deleteRequestedTask(requestedTask.value.id)
  if (response) {
    const msg = `Requested Task <code>${shortId(requestedTask.value.id)}</code> has been deleted.`
    notificationStore.showSuccess(msg)
    requestedTask.value = null
    await fetchRecipeTasks()
  } else {
    for (const error of requestedTasksStore.errors) {
      notificationStore.showError(error)
    }
  }
  workingText.value = null
}

const cloneRecipe = async (newName: string) => {
  const response = await recipeStore.cloneRecipe(props.recipeName, newName)
  if (response) {
    notificationStore.showSuccess(
      `Recipe <code>${newName}</code> has been created off <code>${props.recipeName}</code>.`,
    )
    router.push({ name: 'recipe-detail', params: { recipeName: newName } })
  } else {
    for (const error of recipeStore.errors) {
      notificationStore.showError(error)
    }
  }
}

const fetchRecipeImageTags = async (imageName: string) => {
  const parts = imageName.split('/')
  if (parts.length < 2) {
    return // invalid image_name
  }
  const hubName = parts.splice(parts.length - 2, parts.length).join('/')

  const response = await recipeStore.fetchRecipeImageTags(props.recipeName, {
    hubName: hubName,
  })
  if (response) {
    imageTags.value = response
  } else {
    for (const error of recipeStore.errors) {
      notificationStore.showError(error)
    }
  }
}

const updateRecipe = async (update: RecipeUpdateSchema) => {
  const response = await recipeStore.updateRecipe(props.recipeName, update)
  if (response) {
    notificationStore.showSuccess('Recipe updated successfully')
    // if name changed, redirect to the new recipe
    if (update.name) {
      router.push({
        name: 'recipe-detail-tab',
        params: { recipeName: update.name, selectedTab: 'edit' },
      })
    }
    // update the recipe in the current view
    const updatedRecipe = await recipeStore.fetchRecipe(update.name || props.recipeName, true)
    if (updatedRecipe) {
      recipe.value = updatedRecipe
    } else {
      for (const error of recipeStore.errors) {
        notificationStore.showError(error)
      }
    }

    // if context was changed, fetch the new contexts
    if (update.context !== null || update.context !== undefined) {
      const newContexts = await contextStore.fetchContexts()
      if (newContexts) {
        contexts.value = newContexts
      } else {
        for (const error of contextStore.errors) {
          notificationStore.showError(error)
        }
      }
    }
  } else {
    for (const error of recipeStore.errors) {
      notificationStore.showError(error)
    }
  }
}

const validateRecipe = async () => {
  await recipeStore.validateRecipe(props.recipeName)
  if (recipeStore.errors.length > 0) {
    for (const error of recipeStore.errors) {
      notificationStore.showError(error)
    }
  }
}

// History-related methods
const loadHistory = async ({ limit, skip }: { limit: number; skip: number }) => {
  if (skip > 0 && !canLoadMoreHistory.value) return

  loadingHistory.value = true
  try {
    await recipeHistoryStore.fetchHistory(props.recipeName, limit, skip)
  } catch (error) {
    console.error('Failed to load history items', error)
    notificationStore.showError(`Failed to ${skip > 0 ? 'load more' : 'load'} history items`)
  } finally {
    loadingHistory.value = false
  }
}

const deleteRecipe = async () => {
  const response = await recipeStore.deleteRecipe(props.recipeName)
  if (response) {
    notificationStore.showSuccess(`Recipe <code>${props.recipeName}</code> has been deleted.`)
    router.push({ name: 'recipes-list' })
  } else {
    for (const error of recipeStore.errors) {
      notificationStore.showError(error)
    }
  }
}

const archiveRecipe = async (comment?: string) => {
  const response = await recipeStore.archiveRecipe(props.recipeName, comment)
  if (response) {
    notificationStore.showSuccess(`Recipe <code>${props.recipeName}</code> has been archived.`)
    // Refresh the recipe data to update the archive status
    await refreshData(true)
    // Switch to info tab after archiving
    currentTab.value = 'details'
  } else {
    for (const error of recipeStore.errors) {
      notificationStore.showError(error)
    }
  }
}

const restoreRecipe = async (comment?: string) => {
  const response = await recipeStore.restoreRecipe(props.recipeName, comment)
  if (response) {
    notificationStore.showSuccess(`Recipe <code>${props.recipeName}</code> has been restored.`)
    // Refresh the recipe data to update the archive status
    await refreshData(true)
    // Switch to info tab after restoring
    currentTab.value = 'details'
  } else {
    for (const error of recipeStore.errors) {
      notificationStore.showError(error)
    }
  }
}

const handleRevert = async () => {
  // Reload recipe data after revert
  await refreshData(true, true)
}

const refreshData = async (forceReload: boolean = false, fetchHistory: boolean = false) => {
  // Only set ready to false if we don't have any data yet
  if (!recipe.value) {
    ready.value = false
  }

  // Load recipe data (force reload on edit tab or explicitly requested)
  const response = await recipeStore.fetchRecipe(
    props.recipeName,
    currentTab.value === 'edit' || forceReload,
  )
  if (response) {
    recipe.value = response
  } else {
    error.value = 'Failed to load recipe data'
  }

  if (recipe.value) {
    if (recipe.value.enabled) {
      await fetchWorkers()
    }
    await fetchRecipeTasks()

    if (fetchHistory) {
      recipeHistoryStore.clearHistory()
      await loadHistory({ limit: recipeHistoryStore.paginator.limit, skip: 0 })
    }
    if (forceReload) {
      offlinerVersions.value =
        (await offlinerStore.fetchOfflinerVersions(recipe.value.offliner)) || []
    }
    ready.value = true
  }
}

const shortId = (id: string | null): string => {
  return id ? id.substring(0, 8) : ''
}

const calculateTaskDuration = (task: TaskLight): string => {
  if (!task.timestamp) return ''
  const started = getTimestampStringForStatus(task.timestamp, 'started', '')
  if (!started) return 'Not actually started ⌛'

  const completed = getTimestampStringForStatus(
    task.timestamp,
    'succeeded',
    getTimestampStringForStatus(task.timestamp, 'failed', ''),
  )
  if (!completed) return 'Not actually completed ⌛'

  return formatDurationBetween(started, completed)
}

const handleOfflinerChange = async (offliner: string) => {
  // fetch all the offliner versions
  const response = (await offlinerStore.fetchOfflinerVersions(offliner)) || []
  if (response) {
    offlinerVersions.value = response
  } else {
    for (const error of offlinerStore.errors) {
      notificationStore.showError(error)
    }
  }
  // Child component will choose a default version (if needed) and emit
  // @offliner-version-change, which we handle via handleOfflinerVersionChange.
}

const handleOfflinerVersionChange = async (offliner: string, version: string) => {
  // fetch the offliner definition
  const response = await offlinerStore.fetchOfflinerDefinitionByVersion(offliner, version)
  if (response) {
    flagsDefinition.value = response.flags
    helpUrl.value = response.help
  } else {
    for (const error of offlinerStore.errors) {
      notificationStore.showError(error)
    }
  }
}

// Lifecycle
onMounted(async () => {
  // Redirect to details if trying to access restricted tabs without permission
  if (
    (props.selectedTab === 'edit' || props.selectedTab === 'history') &&
    !canUpdateRecipes.value
  ) {
    router.push({ name: 'recipe-detail', params: { recipeName: props.recipeName } })
  }

  // just in case the data is not loaded yet rather than using
  // .... computed(() => store.value. Given these stores cache values,
  // we can be sure that the data is already loaded on app mount.
  // Or we fetch again here (if for some reason, say network connection is slow)
  // and we couldn't fetch on app mount.
  tags.value = (await tagStore.fetchTags()) || []
  contexts.value = (await contextStore.fetchContexts()) || []
  languages.value = (await languageStore.fetchLanguages()) || []
  offliners.value = (await offlinerStore.fetchOffliners()) || []
  platforms.value = (await platformStore.fetchPlatforms()) || []
  // after fectching the all the data, we can fetch the offliner definition
  await refreshData(true, props.selectedTab === 'history')
  if (recipe.value) {
    const offlinerDefinition = await offlinerStore.fetchOfflinerDefinitionByVersion(
      recipe.value.offliner,
      recipe.value.version,
    )
    if (offlinerDefinition) {
      helpUrl.value = offlinerDefinition.help
      flagsDefinition.value = offlinerDefinition.flags
    }
    await fetchRecipeImageTags(recipe.value.config.image.name)
    // Get validation errors about the recipe on mount
    if (!recipe.value.is_valid) {
      await validateRecipe()
    }
  }
})

onUnmounted(() => {
  // Clear recipe history to prevent accumulation of history items
  recipeHistoryStore.clearHistory()
})

// Watch for tab changes
watch(
  () => props.selectedTab,
  async (newTab) => {
    currentTab.value = newTab
    // Only refresh data if we don't have any data yet, or if not cloning or archiving
    if (!recipe.value || !['clone', 'archive', 'delete'].includes(newTab)) {
      await refreshData(newTab === 'edit', newTab === 'history')
    }
    if (newTab === 'similar' && recipe.value) {
      await loadSimilar(recipeStore.paginator.limit, recipeStore.paginator.skip)
    }
  },
)

// Watch for recipe name changes (when navigating to a different recipe)
watch(
  () => props.recipeName,
  async () => {
    // Reset the current tab to details when switching recipes
    // Clear current data and reload the new recipe
    recipe.value = null
    currentTab.value = 'details'
  },
)
</script>

<style scoped>
.align-top {
  vertical-align: top;
}
</style>
