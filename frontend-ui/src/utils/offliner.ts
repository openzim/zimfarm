import constants from '@/constants'
import type { WorkerScheduleDuration } from '@/types/base'
import type { OfflinerDefinition } from '@/types/offliner'
import type { ExpandedScheduleConfig, ScheduleConfig } from '@/types/schedule'
import type { Task, TaskLight } from '@/types/tasks'
import { getTimestampStringForStatus } from '@/utils/timestamp'
import { DateTime } from 'luxon'
import { formatDurationBetween } from './format'

export function getSecretFields(offlinerDefinition: OfflinerDefinition[] | null) {
  if (offlinerDefinition === null) return []
  return offlinerDefinition
    .filter(function (item) {
      return 'secret' in item && item.secret === true
    })
    .map(function (item) {
      return item.data_key
    })
}

export function imageHuman(config: ScheduleConfig | ExpandedScheduleConfig) {
  return config.image.name + ':' + config.image.tag
}

export function imageUrl(config: ScheduleConfig | ExpandedScheduleConfig) {
  const prefix =
    config.image.name.indexOf('ghcr.io') != -1 ? 'https://' : 'https://hub.docker.com/r/'
  return prefix + config.image.name
}

export function buildDockerCommand(name: string, config: ExpandedScheduleConfig) {
  const mounts = ['-v', '/my-path:' + config.mount_point + ':rw']
  const mem_params = ['--memory-swappiness', '0', '--memory', config.resources.memory.toString()]
  const capadd_params: string[] = []
  const capdrop_params: string[] = []
  if (config.resources.cap_add) {
    config.resources.cap_add.forEach(function (cap) {
      capadd_params.push('--cap-add')
      capadd_params.push(cap)
    })
  }
  if (config.resources.cap_drop) {
    config.resources.cap_drop.forEach(function (cap) {
      capdrop_params.push('--cap-drop')
      capdrop_params.push(cap)
    })
  }
  let shm_params: string[] = []
  if (config.resources.shm) shm_params = ['--shm-size', config.resources.shm.toString()]
  const cpu_params = [
    '--cpu-shares',
    (config.resources.cpu * constants.DEFAULT_CPU_SHARE).toString(),
  ]
  const docker_base = ['docker', 'run']
    .concat(mounts)
    .concat(['--name', config.offliner.offliner_id + '_' + name, '--detach'])
    .concat(cpu_params)
    .concat(mem_params)
    .concat(shm_params)
    .concat(capadd_params)
    .concat(capdrop_params)
  const scraper_command = buildCommandWithout(config)
  const args = docker_base.concat([imageHuman(config)]).concat([scraper_command])
  return args.join(' ')
}

export function buildCommandWithout(config: ExpandedScheduleConfig) {
  return config.str_command
}

interface SingleScheduleDuration {
  single: boolean
  value: number
  formattedDuration: string
  worker: string
  on: string
  formattedMinDuration: null
  formattedMaxDuration: null
  minWorkers: null
  maxWorkers: null
}

interface MultipleScheduleDuration {
  single: false
  formattedMinDuration: string
  formattedMaxDuration: string
  formattedDuration: string
  minWorkers: WorkerScheduleDuration[]
  maxWorkers: WorkerScheduleDuration[]
}

export function buildScheduleDuration(
  historyRuns: TaskLight[],
): SingleScheduleDuration | MultipleScheduleDuration | null {
  if (!historyRuns || historyRuns.length === 0) return null

  // Calculate duration for each task
  const taskDurations: Array<{
    duration: number
    formattedDuration: string
    worker: string
    on: string
    task: TaskLight
  }> = []

  for (const task of historyRuns) {
    if (!task.timestamp) continue

    const first = getTimestampStringForStatus(task.timestamp, 'started', '')
    if (!first) continue

    const startTime = DateTime.fromISO(first).toMillis()
    const endTime = DateTime.fromISO(task.updated_at).toMillis()

    taskDurations.push({
      duration: endTime - startTime,
      formattedDuration: formatDurationBetween(first, task.updated_at),
      worker: task.worker_name,
      on: task.updated_at,
      task,
    })
  }

  if (taskDurations.length === 0) return null

  // Find min and max durations
  const minTask = taskDurations.reduce((min, current) =>
    current.duration < min.duration ? current : min,
  )
  const maxTask = taskDurations.reduce((max, current) =>
    current.duration > max.duration ? current : max,
  )

  // If all tasks have the same duration, return single duration
  if (minTask.duration === maxTask.duration) {
    return {
      single: true,
      value: minTask.duration,
      formattedDuration: minTask.formattedDuration,
      worker: minTask.worker,
      on: minTask.on,
      formattedMinDuration: null,
      formattedMaxDuration: null,
      minWorkers: null,
      maxWorkers: null,
    }
  }

  // Group workers by duration for min/max, ensuring no duplicate workers
  const minWorkerMap = new Map<
    string,
    { value: number; on: string; worker_name: string; default: boolean; formattedDuration: string }
  >()
  const maxWorkerMap = new Map<
    string,
    { value: number; on: string; worker_name: string; default: boolean; formattedDuration: string }
  >()

  taskDurations.forEach((t) => {
    if (t.duration === minTask.duration) {
      minWorkerMap.set(t.worker, {
        value: t.duration,
        formattedDuration: t.formattedDuration,
        on: t.on,
        worker_name: t.worker,
        default: false,
      })
    }
    if (t.duration === maxTask.duration) {
      maxWorkerMap.set(t.worker, {
        value: t.duration,
        formattedDuration: t.formattedDuration,
        on: t.on,
        worker_name: t.worker,
        default: false,
      })
    }
  })

  return {
    single: false,
    formattedMinDuration: minTask.formattedDuration,
    formattedMaxDuration: maxTask.formattedDuration,
    formattedDuration: maxTask.formattedDuration,
    minWorkers: Array.from(minWorkerMap.values()),
    maxWorkers: Array.from(maxWorkerMap.values()),
  }
}

export function logsUrl(task: Task) {
  return uploadUrl(task.upload.logs.upload_uri, task.container.log)
}

export function artifactsUrl(task: Task) {
  if (!(task.upload.artifacts && task.container.artifacts)) return ''
  return uploadUrl(task.upload.artifacts.upload_uri, task.container.artifacts)
}

function uploadUrl(uri: string, filename: string) {
  let url = new URL(uri)
  const scheme = url.protocol.replace(/:$/, '')

  if (['http', 'https'].indexOf(scheme) == -1)
    url = new URL(url.href.replace(new RegExp('^' + url.protocol), 'https:'))

  if (scheme == 's3') {
    let log_url = url.protocol + '//' + url.host + url.pathname
    const bucketName = url.searchParams.get('bucketName')
    if (bucketName) log_url += bucketName + '/'
    return log_url + filename
  }

  return filename
}
