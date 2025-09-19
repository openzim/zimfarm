import constants from '@/constants'
import type { ScheduleDuration, WorkerScheduleDuration } from '@/types/base'
import type { OfflinerDefinition } from '@/types/offliner'
import type { ExpandedScheduleConfig, ScheduleConfig } from '@/types/schedule'
import type { Task, TaskLight } from '@/types/tasks'
import { formatDuration, formatDurationBetween } from '@/utils/format'
import { DateTime } from 'luxon'
import { getTimestampStringForStatus } from './timestamp'

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
  single: true
  value: number
  formattedDuration: string
  worker: string
  on: string
}

interface MultipleScheduleDuration {
  single: false
  formattedMinDuration: string
  formattedMaxDuration: string
  minWorkers: WorkerScheduleDuration[]
  maxWorkers: WorkerScheduleDuration[]
}
export function single_duration(value: number, worker: string, on: string): SingleScheduleDuration {
  return {
    single: true,
    value: value,
    formattedDuration: formatDuration(value * 1000),
    worker: worker,
    on: on,
  }
}

export function buildScheduleDuration(
  duration: ScheduleDuration | null,
): SingleScheduleDuration | MultipleScheduleDuration | null {
  if (!duration) return null

  if (!duration.available && duration.default) {
    return single_duration(duration.default.value, 'default', duration.default.on)
  }

  if (!duration.workers) return null

  const workersArray = Object.values(duration.workers)
  const minWorker = workersArray.reduce(
    (min, worker) => (worker.value < min.value ? worker : min),
    workersArray[0],
  )
  const maxWorker = workersArray.reduce(
    (max, worker) => (worker.value > max.value ? worker : max),
    workersArray[0],
  )

  if (minWorker == maxWorker && minWorker.worker_name) {
    return single_duration(
      duration.workers[minWorker.worker_name].value,
      minWorker.worker_name,
      duration.workers[minWorker.worker_name].on,
    )
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

  workersArray.forEach((worker) => {
    if (worker.value == minWorker.value) {
      minWorkerMap.set(worker.worker_name || 'default', {
        value: worker.value,
        on: worker.on,
        worker_name: worker.worker_name || 'default',
        default: worker.default,
        formattedDuration: formatDuration(worker.value * 1000),
      })
    }
    if (worker.value == maxWorker.value) {
      maxWorkerMap.set(worker.worker_name || 'default', {
        value: worker.value,
        on: worker.on,
        worker_name: worker.worker_name || 'default',
        default: worker.default,
        formattedDuration: formatDuration(worker.value * 1000),
      })
    }
  })

  const minWorkers = Array.from(minWorkerMap.values())
  const maxWorkers = Array.from(maxWorkerMap.values())

  return {
    single: false,
    formattedMinDuration: minWorkers[0].formattedDuration,
    formattedMaxDuration: maxWorkers[0].formattedDuration,
    minWorkers: minWorkers,
    maxWorkers: maxWorkers,
  }
}

export function buildTotalDurationDict(
  historyRuns: TaskLight[],
): SingleScheduleDuration | MultipleScheduleDuration | null {
  // compute the total duration of each task from started to completed
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

    const started = getTimestampStringForStatus(task.timestamp, 'started', '')
    if (!started) continue

    const succeeded = getTimestampStringForStatus(task.timestamp, 'succeeded', '')
    if (!succeeded) continue

    const startTime = DateTime.fromISO(started).toMillis()
    const endTime = DateTime.fromISO(succeeded).toMillis()

    taskDurations.push({
      duration: endTime - startTime,
      formattedDuration: formatDurationBetween(started, succeeded),
      worker: task.worker_name,
      on: task.updated_at,
      task,
    })
  }
  if (taskDurations.length === 0) return null

  // Find min and max durations from started to succeeded
  const minTask = taskDurations.reduce(
    (min, current) => (current.duration < min.duration ? current : min),
    taskDurations[0],
  )
  const maxTask = taskDurations.reduce(
    (max, current) => (current.duration > max.duration ? current : max),
    taskDurations[0],
  )

  // If all tasks have the same duration, return single duration
  if (minTask.duration === maxTask.duration) {
    return single_duration(minTask.duration, minTask.worker, minTask.on)
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
