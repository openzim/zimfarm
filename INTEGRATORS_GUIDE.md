# Zimfarm Integrators Guide

This guide is intended for **integrators and system administrators** who are looking
to install, configure, deploy, and maintain the Zimfarm platform infrastructure.

If you are looking for a high-level overview of how Zimfarm behaves, what recipes,
tasks, workers, and offliners are, or how the task assignment algorithm works, please
read the [EDITORS_GUIDE.md](EDITORS_GUIDE.md) first. It provides the conceptual
foundation for how the platform operates from a user's perspective.

The zimfarm is made of several components and each component is packaged as a Docker
image. Each image is meant to be deployed as a Docker container and some of them require
other components to be running in order to function properly.
For inspiration and practical examples on how to wire all these components together,
we highly recommend looking at the `dev/` folder. It contains a complete
`docker-compose.yml` stack used for local development, which demonstrates exactly how
the containers interact, how volumes are mounted, and how environment variables are
passed. It also contains shell scripts to set up worker accounts, retreive offliner
definitions, create SSH keys for authentication and more.

## Table of Contents

- [Architecture & Components Overview](#architecture--components-overview)
  - [Backend](#backend)
  - [Frontend UI](#frontend-ui)
  - [Worker](#worker)
  - [Receiver](#receiver)
  - [Monitor](#monitor)
  - [Healthcheck](#healthcheck)
  - [Watcher](#watcher)
- [User Management & Roles](#user-management--roles)
- [Notifications](#notifications)
- [External Dependencies & Requirements](#external-dependencies--requirements)
- [Integrations](#integrations)

## Architecture & Components Overview

Instead of a single monolithic application, the platform is divided into specialized
components that communicate over standard protocols (HTTP/REST, SSH/SFTP). Below is
a detailed breakdown of the core components required to run the farm, alongside their
primary configuration environment variables.

### Backend

The backend (located in the `backend` folder at the project root) is the central
nervous system of the Zimfarm. It is built with Python, FastAPI, and backed by
a PostgreSQL database. The backend is composed of two different services packaged into
two distinct Docker images.

- a RESTful API that all other components (and end-users) interact with.
- a background service (called `background-tasks`) that performs tasks like requesting
  tasks periodically and more.

The backend is responsible for:

- persisting users, workers, recipes, and tasks.
- handling requests to create intermediary "requested tasks" from a recipe's configuration
- assigning available requested tasks to workers based on a sophisticated matching algorithm.
- exposing background tasks to
  - cancel/remove old and stale tasks
  - requests tasks periodically
  - clean up orphaned database records and
  - notify external systems (like the OpenZIM CMS) when new ZIM files are available.

**Key Environment Variables:**

- `POSTGRES_URI`: The connection string for the database (e.g., `postgresql://user:pass@host/db`).
- `ZIM_UPLOAD_URI`: The destination to upload ZIM's. See the `dev/docker-compose.yml`
  environment variables for the different upload URIs and the different schemes
  they can take.
- `ENABLED_SCHEDULER`: Set to `"true"` to enable the background task that creates
  requested tasks from active recipes. When set to false, it also prevents the
  backend from creating tasks from requested tasks.
- `USES_WORKERS_IPS_WHITELIST`: Set to `"true"` if your architecture relies on strict IP whitelisting for worker nodes.
- `INFORM_CMS`: Set to `"true"` to notify the OpenZIM CMS upon successful task
  completion. A task is successfully completed if it exits successfully and it's uploads
  are successful.
- `CMS_BASE_URL`: The URL of the CMS to notify (e.g., `https://cms.openzim.org`).
- `ZIMCHECK_OPTION`: Whether to run zimcheck utility against produced ZIMs. This verifies
  that a given ZIM file is not corrupted. In addition, it provides many features to
  secure that ZIM entries are proper and properly linked.
- `DISABLE_WAREHOUSE_PATH`: Whether to ignore the warehouse path in a recipe while requesting a task. When this is set to `"true"` and `ZIMCHECK_OPTION` is not set, the API
  will fail to start. This is because this option is used to communicate to the worker
  to keep ZIM's at the receiver root. In addition, the worker uses this information
  to rename a ZIM file to the form `<zim_uuid>.zim` to prevent collisions since everything
  will be placed at the root folder.
- `ALEMBIC_UPGRADE_HEAD_ON_START`: whether to apply alembic migrations on application
  start. It is recommended to set this to `"true"` on the background tasks container
  and `"false"` on the API.
- `BLOB_PRIVATE_STORAGE_URL` / `BLOB_PUBLIC_STORAGE_URL`: Endpoints used for storing blobs (images, html, css, etc) of recipes.
- `MAILGUN_API_KEY` / `MAILGUN_API_URL`: Credentials for dispatching email alerts.
- `SLACK_URL`: Webhook URL for posting notifications to Slack.
- `REQUESTS_TIMEOUT`: Global HTTP request timeout limit (e.g., `30s`).

**NOTE**: See the `dev/docker-compose.yml` file to see reasonable defaults for some of
these environment variables.

### Frontend UI

The frontend (located in the `frontend-ui` directory of the project root) is a Vue.js 3
single-page application (SPA). It serves as the visual dashboard for human operators,
editors, and administrators. Because it is purely a client-side application, it
strictly relies on the Backend API to fetch and mutate data. Through the UI, users can
create recipes, monitor real-time task progress, cancel stuck tasks, and oversee the
fleet of connected workers.

**Key Environment Variables:**
Unlike server-side components, the frontend requires its environment configuration to
be injected at runtime so the browser can read it. This is typically done via the
`public/config.json.js` file:

- `ZIMFARM_WEBAPI`: The public-facing URL of your Backend API so the frontend knows where to send requests (e.g., `https://api.farm.openzim.org/v2`).
- `ZIMFARM_ZIM_DOWNLOAD_URL`: The URL of the server where the ZIMs are stored
- `MONITORING_URL`: The URL of the [Netdata server](https://www.netdata.cloud/) where
  monitoring statistics are stored
- `OAUTH_CLIENT_ID`: Oauth client ID for authentication (currently backed by [Ory.sh](https://www.ory.com/))

See the `dev/frontend-ui/public/config.json` for some reasonable defaults of these variables.

### Worker

The worker (located in the `worker` directory of the project root) acts as the
execution node of the farm. This is executed on dedicated machines (or VMs) called `workers`. Scrapers are run on these worker machines to create ZIM files, upload them and
accompanying logs and artifiacts to a central location so that we have a distributed
workload. Because processing ZIM files requires dynamic container orchestration, the
worker heavily utilizes the Docker SDK. It is conceptually split into two distinct
roles that run on the same physical host:

1. **Worker Manager**: This is the daemon that constantly runs on the server. It
   authenticates with the backend using an SSH private key, reports its available hardware
   resources (CPU, RAM, Disk), and continuously polls the `/requested-tasks/worker`
   endpoint for new work. When the backend assigns a task, the Manager spawns a
   "Task Worker" container to handle it and configures necessary settings for it.
2. **Task Worker**: This ephemeral container is spawned for _each specific task_. It
   reads the task's configuration and orchestrates the actual scraper offliner container
   (e.g., `mwoffliner`, `youtube`). It
   - monitors the scraper's stdout/stderr
   - reports progress states back to the backend API
   - starts a monitor container if the task has monitoring enabled
   - starts uploader containers for logs, artifacts and ZIM files
   - starts the zimcheck container if the task is configured to run with a `ZIMCHECK_OPTION`
   - manages cleanup once the scraper finishes or fails.
     To achieve some of these objectives, the Task Worker will orchestrate multiple child
     containers:
   - the scraper to create the ZIM
   - a monitor child (if task has monitoring enabled) to stream resource usage during execution of the task
     to a monitor parent
   - multiple upload containers to respectively upload ZIM, logs and optional artifacts
   - a DNS cache container to cache DNS requests for scrapers
   - a zimcheck container if task requires zimcheck. The zimcheck tool verifies that a
     given ZIM file is not corrupted. In addition, it provides many features to ensure
     that ZIM entries are proper and properly linked.

**NOTE**: Currently, workers only communicate with the backend API only via standard
HTTP requests. As such, they poll the API at configured intervals to see if there are
tasks to do.

**Key Environment Variables:**

- `ZIMFARM_USERNAME`: The username of the account that owns this worker node.
- `PRIVATE_KEY`: Path to the SSH private key used to cryptographically prove the
  worker's identity to the backend API as workers authenticate with SSH key and not password.
- `WEB_API_URI`: The URL to the Backend API.
- `ZIMFARM_CPUS`: CPU shares available to this worker (e.g., `6`).
- `ZIMFARM_MEMORY`: Total RAM the worker is allowed to allocate to tasks (e.g., `4G`).
- `ZIMFARM_DISK`: Total disk space available for task execution (e.g., `100G`).
- `SELFISH`: Set to `"true"` if this worker should _only_ execute tasks explicitly assigned to it. All other tasks are ignored.
- `CORDONED`: Set to `"true"` to temporarily prevent the backend from assigning
  new tasks to this worker (useful for graceful shutdown/maintenance).
- `OFFLINERS`: A comma-separated list of scrapers this worker supports.
  Leave empty to support all.
- `PLATFORM_<name>_MAX_TASKS`: Enforces concurrency limits for specific platforms to avoid rate limits (e.g., `PLATFORM_youtube_MAX_TASKS=1`).
- `TASK_WORKER_IMAGE`, `DNSCACHE_IMAGE`, `UPLOADER_IMAGE`, `MONITOR_IMAGE`: Explicit Docker image tags the worker should use when spawning child containers.

**NOTE**: See the `dev/docker-compose.yml` file for reasonable defaults of these environment variables

### Receiver

The receiver (located at the `receiver` directory of the project root) is a hardened
SFTP ingestion server responsible for safely accepting ZIM files uploaded by workers.
It leverages OpenSSH and Jailkit to restrict access.

Instead of maintaining standard local user accounts, the receiver dynamically
authenticates incoming connections using OpenSSH's `AuthorizedKeysCommand`. When a
worker tries to upload a file, the receiver takes the worker's SSH key signature,
queries the Zimfarm Backend API to retrieve the worker's public keys. Once authenticated,
the worker is dropped into a jailed environment where files are moved into their final warehouse paths. See the `receiver/README.md` for a more descriptive description of the
behaviour of the receiver and the variables it supports.

**Key Environment Variables:**

- `ZIMFARM_WEBAPI`: URL to the Backend API, used by the receiver script to validate incoming SSH keys.
- `ZIMFARM_USERNAME`: The username of the account that should validate worker's SSH key fingerprints.

### Monitor

The Zimfarm monitoring infrastructure is built on [Netdata](https://www.netdata.cloud/),
a distributed, real-time performance and health monitoring system. The monitoring setup
consists of two distinct components that work together to provide observability across
the entire farm:

- **Monitor Parent**: A single Netdata instance that serves as the central aggregation
  where all metrics from distributed workers are collected and made accessible to
  users through a Web interface. The parent is configured to retrieve the list of workers and the fingerprint of their SSH keys from the backend API. This fingerepint is used
  to create a stream configuration for each worker. It is important to note that this configuration is done by a script scheduled via cron to allow it get the updated list of
  workers without restart.
- **Monitor Child**: Optional Netdata agents dynamically spawned on worker nodes to
  monitor individual scraper tasks. Each child streams real-time resource metrics (CPU,
  memory, disk I/O, etc) of the containers it spawns (including the scraper) to the parent. The frontend UI provides a link to the parent's web interface where users can view the
  aggregated metrics and analyze task performance data.

**NOTE**: There should be one and only one monitor parent.

**Deployment Considerations:**

- Deploy the Monitor Parent on a stable, always-on server (not on worker nodes that
  may be ephemeral or scaled down).
- Ensure adequate storage for historical metrics based on your retention policy and
  the number of concurrent tasks you expect to monitor. See the `monitor/parent/README.md` file for more information.
- The parent must be network-accessible from all worker nodes on the Netdata streaming
  port (default: `19999`).
- Configure the Frontend UI's `MONITORING_URL` environment variable to point to the
  Monitor Parent's public URL so users can access the dashboard.

**Key Environment Variables:**
For the monitor parent, the key environment variables are:

- ZIMFARM_API_URL: the URL of the backend API
- ZIMFARM_USERNAME: the username to be used to retrieve the list of workers and the
  fingerprints of their SSH keys.
- ZIMFARM_PASSWORD: password of the zimfarm user

The monitor parent typically requires custom configuration
files to enable streaming mode and configure retention policies. These are usually
mounted as volumes into the container. See the `monitor/parent/README.md` file for a complete example of how to configure the monitor parent

The configuration of the monitor child is set by the task worker which configures
the `MONITORING_DEST`, the URL of the monitor parent.

**Docker Privileges Required:**

To successfully monitor host-level and container-level metrics, the monitor cHild
requires **specific Docker privileges and volume mounts**:

- **Privileged Mode or Specific Capabilities**: The container may need to run in
  privileged mode (`--privileged`) or be granted specific capabilities like
  `SYS_PTRACE`, `SYS_ADMIN`, and `NET_ADMIN` to access system metrics and inspect
  other containers.
- **Host PID Namespace**: Access to the host's PID namespace (`--pid=host`) is often
  required to monitor processes and calculate accurate CPU metrics.
- **Docker Socket Mount**: The Docker socket (`/var/run/docker.sock`) must be mounted
  into the monitor child container so it can query container metadata and stats via
  the Docker API.
- **Proc and Sys Mounts**: Read-only mounts of `/proc` and `/sys` from the host are
  necessary to collect system-level performance data.
- **Cgroup Mounts**: Mount the host's cgroup filesystem (e.g., `/sys/fs/cgroup`) to
  enable per-container resource tracking.

### Healthcheck

The healthcheck service (located in the `healthcheck` directory of the project root) is a
monitoring and diagnostic tool that provides a centralized view of the zimfarm platform's operational health.
Built with Python and FastAPI, it checks the status of components and displays results via an HTML dashboard.

The healthcheck service performs the following validations:

- **Authentication**: Verifies that credentials can successfully authenticate against the Backend API
- **Database Connection**: Tests connectivity to the PostgreSQL database
- **Frontend Availability**: Confirms the frontend UI is accessible and responding
- **Worker Status**: Queries the Backend API to check if workers are online and reporting
- **Upload Status**: Monitors the success rate of log and artifact uploads from recent tasks
- **CMS Integration** (optional): Checks if the OpenZIM CMS is reachable and monitors for pending notifications that haven't been delivered

The service returns an HTTP 200 (OK) status when all checks pass, or HTTP 503 (Service Unavailable) when any component reports an issue.

**Key Environment Variables:**

- `ZIMFARM_API_URL`: URL to the Backend API for querying system status
- `ZIMFARM_FRONTEND_URL`: URL to the Frontend UI for availability checks
- `ZIMFARM_USERNAME`: Username for authenticating with the backend API
- `ZIMFARM_PASSWORD`: Password for the healthcheck user account
- `ZIMFARM_DATABASE_URL`: PostgreSQL connection string for direct database health checks
- `CMS_API_URL`: URL to the OpenZIM CMS API
- `CMS_ENABLED`: Set to `"true"` to include CMS checks in the overall health status. When `"false"`, CMS failures won't affect the global health status
- `CMS_PENDING_THRESHOLD`: Maximum age for pending CMS notifications before flagging as unhealthy (e.g., `24h`)
- `REQUESTS_TIMEOUT`: Timeout for HTTP requests to external services

### Watcher

The watcher (located in the `watcher` directory of the project root) is a specialized
automation component designed to keep StackExchange dumps synchronized and up-to-date
for `sotoki` recipes. It continuously monitors Archive.org for new StackExchange data
dumps, mirrors them to faster S3 storage, and automatically triggers recipe execution
when new dumps become available.

The watcher runs as a long-lived daemon process and handles version detection based on file modification timestamps, deduplication, and intelligent scheduling to avoid triggering tasks for dumps already in use.

**Key Environment Variables:**

- `S3_URL`: S3 storage URL with credentials for uploading dumps (e.g., `https://s3.amazonaws.com/?keyId=...&secretAccessKey=...`)
- `ZIMFARM_API_URL`: URL to the Backend API for scheduling recipes (default: `https://api.farm.openzim.org/v1`)
- `ZIMFARM_USERNAME`: Username for authenticating with the Zimfarm API
- `ZIMFARM_PASSWORD`: Password for the watcher's Zimfarm account
- `DOWNLOAD_URL_BASE`: Base URL for Archive.org downloads (default: `https://archive.org/download`)
- `QUERY_URL`: Archive.org search query to find the latest StackExchange dumps

## User Management & Roles

Zimfarm implements a role-based access control (RBAC) system to manage user permissions
across the platform. Users authenticate via local credentials or OAuth/OIDC, and their
assigned role determines what actions they can perform on recipes, tasks, workers,
and other resources.

### Authentication Methods

The backend supports multiple authentication modes, controlled by the `AUTH_MODES`
environment variable (comma-separated list):

- **`local`**: Traditional username/password authentication.
- **`oauth-oidc`**: OpenID Connect authentication flow.
- **`oauth-session`**: OAuth session-based authentication.

Both `oauth-oidc` and `oauth-session` are backed by [Ory.sh](https://www.ory.com/)

When integrating with an external identity provider (like Kiwix SSO), configure:

- `OAUTH_JWKS_URI`: The JWKS endpoint for token verification
- `OAUTH_ISSUER`: The OAuth issuer URL
- `OAUTH_OIDC_CLIENT_ID`: Your OAuth client identifier
- `CREATE_NEW_OAUTH_ACCOUNT`: Set to `"true"` to automatically create viewer accounts
  for new OAuth users on first login

Users authenticated via OAuth are identified by their `idp_sub` (identity provider subject ID).
Local users authenticate with username/password and workers authenticate using SSH keys.

### Roles & Permissions

Each role grants specific permissions across different resource namespaces. Permissions
are organized into categories: `tasks`, `recipes`, `requested_tasks`, `users`,
`workers`, `zim`, and `offliners`. The table below summarizes what each role can do:

| Role                 | Primary Use Case              | Key Permissions                                                                                                                              |
| -------------------- | ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| **admin**            | System administrators         | Full access to all resources including user management, all CRUD operations on recipes/tasks, worker configuration, and ZIM uploads          |
| **manager**          | Platform managers             | Can manage users, create/update/archive recipes, view and cancel tasks, request tasks, view workers (but cannot delete tasks or upload ZIMs) |
| **editor**           | Content editors               | Can create, update, and archive recipes.                                                                                                     |
| **editor-requester** | Editors who can trigger tasks | Same as editor, but can cancel tasks and create/delete requested tasks                                                                       |
| **worker**           | Worker nodes (machines)       | Can read/update/create tasks, manage requested tasks, register workers, and upload ZIMs. Used by automated worker accounts                   |
| **processor**        | Background processors         | Limited to updating tasks and requested tasks. Designed for automated background services                                                    |
| **viewer**           | Read-only observers           | No permissions. Can authenticate but cannot perform any actions                                                                              |

### Custom Scopes

For fine-grained control beyond predefined roles, administrators can assign custom
permission scopes to individual users. Custom scopes override the default role
permissions and are stored in the user's `scope` field as a JSON object mapping
namespaces to permission sets.

Example custom scope structure:

```sh
{
  "recipes": {
    "read": true,
    "create": true,
    "update": false,
    "delete": false
  }
}
```

When a user has a custom scope, their role field typically shows `"custom"` and their
permissions are evaluated from the scope object rather than the predefined role.

## Notifications

Zimfarm provides a flexible notification system to alert users and teams about task
events. The platform supports multiple delivery channels (email, Slack,
webhooks) and can be configured both globally (for all tasks) and per-recipe (for
specific recipes).

### When Notifications Are Triggered

The notification system recognizes three lifecycle events:

| Event         | Trigger Condition                      | Description                                                                                                   |
| ------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| **requested** | When a requested task is created       | Fired when a recipe generates a new requested task (either manually or via periodic scheduling)               |
| **started**   | When a worker begins executing a task  | Fired when a requested task is assigned to a worker and execution begins                                      |
| **ended**     | When a task reaches any terminal state | Fired when a task completes successfully, fails, or is canceled. This is an alias for all completion statuses |

### Notification Methods

#### Email (via Mailgun)

Email notifications are sent using the Mailgun email service.

**Required Environment Variables:**

- `MAILGUN_API_URL`: Your Mailgun API endpoint (e.g., `https://api.mailgun.net/v3/yourdomain.com`)
- `MAILGUN_API_KEY`: Your Mailgun API key for authentication
- `MAILGUN_FROM`: The sender address for notification emails (e.g., `zimfarm@yourdomain.com`)

**Recipients**: Specified as email addresses (e.g., `admin@example.com`)

#### Slack

Slack notifications post formatted messages to specified channels or direct messages.

**Required Environment Variables:**

- `SLACK_URL`: Your Slack incoming webhook URL
- `SLACK_USERNAME`: (Optional) Display name for the notification bot
- `SLACK_EMOJI`: (Optional) Emoji icon for the bot (e.g., `:robot_face:`)
- `SLACK_ICON`: (Optional) Image URL for the bot avatar

**Recipients**: Specified as Slack targets with `#` prefix for channels (e.g., `#alerts`)
or `@` prefix for direct messages (e.g., `@username`)

#### Webhooks

Webhooks send HTTP POST requests containing the full task data as JSON to specified
URLs.

**Recipients**: Specified as complete HTTP/HTTPS URLs (e.g., `https://api.example.com/zimfarm/webhook`)

#### Global Notifications

Global notifications apply to **all tasks** across the entire farm. They are configured
via environment variables on the Backend API container using the format:

```sh
GLOBAL_NOTIFICATION_<event>=<method>,<target1>,<target2>|<method>,<target3>
```

Where:

- `<event>`: One of `requested`, `started`, or `ended`
- `<method>`: One of `mailgun`, `slack`, or `webhook`
- `<target>`: The recipient (email, Slack channel, or webhook URL)
- Multiple targets for the same method are comma-separated
- Multiple methods are pipe (`|`) separated

**Example:**

```sh
# Email admin on all task completions
GLOBAL_NOTIFICATION_ended=mailgun,admin@example.com

# Slack #operations on starts, email on failures
GLOBAL_NOTIFICATION_started=slack,#operations
GLOBAL_NOTIFICATION_ended=mailgun,oncall@example.com|slack,#alerts

# Webhook integration for all events
GLOBAL_NOTIFICATION_requested=webhook,https://api.example.com/zimfarm/requested
GLOBAL_NOTIFICATION_ended=webhook,https://api.example.com/zimfarm/completed
```

#### Per-recipe Notifications

Individual recipes can define their own notification preferences via the `notification`
field in the recipe configuration. This is useful for routing alerts for specific
content types to the appropriate teams or channels.

Per-recipe notifications are configured through the Backend API when creating or
updating a recipe.

## External Dependencies & Requirements

Zimfarm relies on several external services and infrastructure components to function
properly.

### PostgreSQL Database

The Backend API and background tasks require a PostgreSQL database for persistent
storage of all platform data including users, recipes, tasks, workers, and files.

The `uuid-ossp` extension must be enabled on the database as UUID primary keys are
genereted on the database side.

### Storage Backends for Uploads

#### ZIM Files

**Supported Protocols:**

- **SFTP** (recommended): Upload to receiver component via SSH (e.g., `sftp://uploader@receiver:22/zim/`)
- **S3**: Direct upload to S3-compatible storage (e.g., `s3+https://s3.amazonaws.com/?keyId=...&secretAccessKey=...&bucketName=zims`)

**Configuration:**

- `ZIM_UPLOAD_URI`: Destination for ZIM files (mandatory)
- `ZIM_EXPIRATION`: Days before ZIM files expire (default: `0` for no expiration)

**Recommendation**: Use SFTP with the receiver component for ZIM uploads. The receiver provides additional features like SSH key authentication, jailed environments, and automatic warehouse path organization.

#### Logs

**Supported Protocols:**

- **S3** (recommended): Store in S3-compatible storage (e.g., `s3+https://s3.amazonaws.com/?keyId=...&secretAccessKey=...&bucketName=logs`)
- **SFTP**: Upload via SSH

**Configuration:**

- `LOGS_UPLOAD_URI`: Destination for log files (mandatory)
- `LOGS_EXPIRATION`: Days before logs expire (default: `30`)

**Note**: For S3 storage with Wasabi, expiration only works if bucket retention compliance is activated.

#### Artifacts

Some scrapers produce additional artifacts beyond ZIM files (e.g., WARC files, intermediate data).

**Supported Protocols:**

- **S3**: Store in S3-compatible storage
- **SFTP**: Upload via SSH

**Configuration:**

- `ARTIFACTS_UPLOAD_URI`: Destination for artifact files (optional, default: `None`)
- `ARTIFACTS_EXPIRATION`: Days before artifacts expire (default: `30`)

**Note**: Only configure this if you have scrapers that produce artifacts.

#### Zimcheck Results

When zimcheck verification is enabled, the detailed check results are uploaded separately from logs.

**Supported Protocols:**

- **S3**: Store in S3-compatible storage
- **SFTP**: Upload via SSH

**Configuration:**

- `ZIMCHECK_RESULTS_UPLOAD_URI`: Destination for zimcheck output files (required if zimcheck is enabled)
- `ZIMCHECK_RESULTS_EXPIRATION`: Days before results expire (default: `30`)
- `ZIMCHECK_OPTION`: Zimcheck flags (e.g., `--all`). Set to empty string to disable zimcheck.

### OpenZIM CMS Integration

The OpenZIM Content Management System (CMS) is an external service that catalogs and
manages ZIM files for the library. When enabled, Zimfarm automatically notifies the
CMS about newly created and verified ZIM files.

**Configuration:**

- `INFORM_CMS`: Set to `"true"` to enable CMS notifications (default: `"false"`)
- `CMS_BASE_URL`: URL of the CMS API (default: `https://api.cms.openzim.org/v1`)
- `CMS_USERNAME`: Username for CMS API authentication
- `CMS_PASSWORD`: Password for CMS API authentication

When a task completes successfully and its ZIM file passes zimcheck verification, the background tasks service automatically:

- Waits for zimcheck results to be uploaded
- Sends a notification to the CMS with ZIM metadata and check results
- Retries failed notifications periodically (up to the `CMS_MAXIMUM_RETRY_INTERVAL`)

**Note**: If CMS integration is disabled, ZIM files are still produced and uploaded
but won't be automatically registered in the CMS.

## Integrations

### Zimit Frontend

The zimit-frontend is a web-based user interface for creating on-demand ZIM files from
web archives using the `zimit` scraper. It is a separate application that integrates
with Zimfarm to submit and monitor scraping tasks.

Visit [zimit-frontend](https://github.com/openzim/zimit-frontend) to see more about the project.

### WP1

The WP1 is a Wikipedia 1.0 engine and selection tool for creating curated selections
of Wikipedia articles. It is a separate application that integrates with Zimfarm to
build ZIMs of these selections.

Visit [wp1](https://github.com/openzim/wp1) to see more about the project.
