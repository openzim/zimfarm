<template>
  <v-container class="py-8">
    <v-row justify="center">
      <v-col cols="12" md="10" lg="8">
        <v-card class="pa-6" elevation="2">
          <v-card-title class="d-flex align-center mb-4">
            <h2 class="text-h4 font-weight-bold">Support Zimfarm</h2>
            <img src="/assets/logo.svg" width="32" height="32" class="ml-2" alt="Zimfarm Logo" />
          </v-card-title>

          <v-card-text class="text-body-1">
            <p class="mb-4">
              Zimfarm is
              <a href="https://kiwix.org" target="_blank" class="text-primary text-decoration-none">
                Kiwix</a
              >'s platform for automating the creation and update of
              <a
                href="https://wiki.openzim.org/wiki/ZIM_File_Format"
                target="_blank"
                class="text-primary text-decoration-none"
              >
                ZIM files</a
              >. Thousands of recipes are run by distributed
              <router-link :to="{ name: 'workers' }" class="text-primary text-decoration-none">
                workers</router-link
              >. All day, every day, so you can enjoy offline content.
            </p>

            <v-card variant="outlined" class="mb-4">
              <v-card-title class="text-h6">
                <v-icon class="mr-2">mdi-heart</v-icon>
                Support with Donations
              </v-card-title>
              <v-card-text>
                <p class="mb-0">
                  It is <strong>entirely and only supported by donations</strong>. A few dollars may
                  not mean much for you but will certainly help us a lot: if you can,
                  <a
                    href="https://support.kiwix.org/"
                    target="_blank"
                    class="text-primary text-decoration-none"
                  >
                    consider supporting us
                  </a>
                  — even with the price of a cup of coffee (we love coffee and at times need quite a
                  bit of it).
                </p>
              </v-card-text>
            </v-card>

            <v-card variant="flat" class="mb-2">
              <v-card-title class="text-h6 d-flex align-center">
                <v-icon class="mr-2">mdi-server</v-icon>
                Donate a Worker
              </v-card-title>
              <v-card-text>
                <p>
                  Another way to help is by <strong>donating a worker</strong>: if you have a
                  GNU/Linux system with at least 4 cores, 2GB of RAM and a fixed public IP,
                  <a
                    href="https://github.com/openzim/zimfarm/blob/master/worker/README.md"
                    target="_blank"
                    class="text-primary text-decoration-none"
                  >
                    follow these instructions</a
                  >.
                </p>
                <p>
                  And if you have a headless server you want to give us access to,
                  <a
                    href="mailto:contact+zimfarm@kiwix.org"
                    class="text-primary text-decoration-none"
                  >
                    it's even easier</a
                  >!
                </p>
              </v-card-text>
            </v-card>

            <v-divider class="my-2"></v-divider>

            <p>
              Zimfarm is a Python project hosted
              <a
                href="https://github.com/openzim/zimfarm"
                target="_blank"
                class="text-primary text-decoration-none"
              >
                on Github</a
              >. It is built on top of content-specific scrapers like <strong>mwoffliner</strong>,
              <strong>youtube</strong>, <strong>sotoki</strong>, and others. Check out
              <a
                href="https://github.com/openzim/zimfarm/blob/master/dispatcher/backend/src/common/schemas/offliners/__init__.py"
                target="_blank"
                class="text-primary text-decoration-none"
              >
                OpenZIM's repositories
              </a>
              for a complete list.
            </p>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts"></script>

<style scoped>
.v-card-title h2 {
  margin: 0;
}
</style>
