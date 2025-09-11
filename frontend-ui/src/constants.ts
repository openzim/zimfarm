import type { Config } from '@/config'
import type { InjectionKey } from 'vue'

export default {
  config: Symbol() as InjectionKey<Config>,
  CONTACT_EMAIL: 'contact@kiwix.org',
  TOKEN_COOKIE_NAME: 'auth',
  TOKEN_COOKIE_EXPIRY: '6m', // 6 months
  COOKIE_LIFETIME_EXPIRY: '10y', // 10 years
  TASKS_LOAD_SCHEDULES_DELAY: 100,
  MAX_SCHEDULES_IN_SELECTION_REQUEST: 200,
  // Notification constants
  NOTIFICATION_DEFAULT_DURATION: 5000, // 5 seconds
  NOTIFICATION_ERROR_DURATION: 8000, // 8 seconds for errors
  NOTIFICATION_SUCCESS_DURATION: 3000, // 3 seconds for success
  // User roles
  ROLES: ['admin', 'editor', 'editor-requester', 'manager', 'processor', 'worker'] as const,
  MEMORY_VALUES: [
    536870912, // 512MiB
    1073741824, // 1GiB
    2147483648, // 2GiB
    3221225472, // 3GiB
    4294967296, // 4GiB
    5368709120, // 5GiB
    6442450944, // 6GiB
    7516192768, // 7GiB
    8589934592, // 8GiB
    9663676416, // 9GiB
    10737418240, // 10GiB
    11811160064, // 11GiB
    12884901888, // 12GiB
    13958643712, // 13GiB
    15032385536, // 14GiB
    16106127360, // 15GiB
    17179869184, // 16GiB
    18253611008, // 17GiB
    19327352832, // 18GiB
    20401094656, // 19GiB
    21474836480, // 20GiB
    22548578304, // 21GiB
    23622320128, // 22GiB
    24696061952, // 23GiB
    25769803776, // 24GiB
    26843545600, // 25GiB
    27917287424, // 26GiB
    28991029248, // 27GiB
    30064771072, // 28GiB
    31138512896, // 29GiB
    32212254720, // 30GiB
    33285996544, // 31GiB
    34359738368, // 32GiB
    51539607552, // 48GiB
    53687091200, // 50GB
    60129542144, // 56GB
    68719476736, // 64GiB
    77309411328, // 72GiB
    85899345920, // 80GiB
    94489280512, // 88GiB
    103079215104, // 96GiB
    107374182400, // 100GiB
    111669149696, // 104GiB
    120259084288, // 112GiB
    128849018880, // 120GiB
    137438953472, // 128GiB
  ],
  DISK_VALUES: [
    536870912, // 512MiB
    1073741824, // 1GiB
    2147483648, // 2GiB
    3221225472, // 3GiB
    4294967296, // 4GiB
    5368709120, // 5GiB
    10737418240, // 10GiB
    16106127360, // 15GiB
    21474836480, // 20GiB
    32212254720, // 30GiB
    42949672960, // 40GiB
    53687091200, // 50GiB
    80530636800, // 75GiB
    107374182400, // 100GiB
    134217728000, // 125GiB
    161061273600, // 150GiB
    187904819200, // 175GiB
    214748364800, // 200GiB
    241591910400, // 225GiB
    268435456000, // 250GiB
    295279001600, // 275GiB
    322122547200, // 300GiB
    375809638400, // 350GiB
    429496729600, // 400GiB
    483183820800, // 450GiB
    536870912000, // 500GiB
  ],
  CANCELABLE_STATUSES: [
    'reserved',
    'started',
    'scraper_started',
    'scraper_completed',
    'scraper_killed',
  ],

  DEFAULT_FIRE_PRIORITY: 5,

  CATEGORIES: [
    'devdocs',
    'freecodecamp',
    'gutenberg',
    'ifixit',
    'other',
    'phet',
    'psiram',
    'stack_exchange',
    'ted',
    'openedx',
    'vikidia',
    'wikibooks',
    'wikihow',
    'wikinews',
    'wikipedia',
    'wikiquote',
    'wikisource',
    'wikispecies',
    'wikiversity',
    'wikivoyage',
    'wiktionary',
    'mindtouch',
  ],
  WAREHOUSE_PATHS: [
    '/mindtouch',
    '/libretexts',
    '/devdocs',
    '/freecodecamp',
    '/gutenberg',
    '/ifixit',
    '/other',
    '/phet',
    '/psiram',
    '/stack_exchange',
    '/ted',
    '/mooc',
    '/videos',
    '/vikidia',
    '/wikibooks',
    '/wikihow',
    '/wikinews',
    '/wikipedia',
    '/wikiquote',
    '/wikisource',
    '/wikiversity',
    '/wikivoyage',
    '/wiktionary',
    '/zimit',
    '/.hidden/dev',
    '/.hidden/private',
    '/.hidden/endless',
    '/.hidden/bard',
    '/.hidden/bsf',
    '/.hidden/datacup',
    '/.hidden/custom_apps',
  ],
  PERIODICITIES: ['manually', 'monthly', 'quarterly', 'biannualy', 'annually'],
  DEFAULT_CPU_SHARE: 1024, // used to generate docker cpu-shares
}
