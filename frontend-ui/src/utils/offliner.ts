import constants from '@/constants'
import type { ScheduleDuration, WorkerScheduleDuration } from '@/types/base'
import type { OfflinerDefinition } from '@/types/offliner'
import type { ExpandedScheduleConfig, ScheduleConfig } from '@/types/schedule'
import type { Task } from '@/types/tasks'

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
  worker: string
  on: string
  minValue: null
  maxValue: null
  minWorkers: null
  maxWorkers: null
}

interface MultipleScheduleDuration {
  single: false
  minValue: number
  maxValue: number
  minWorkers: WorkerScheduleDuration[]
  maxWorkers: WorkerScheduleDuration[]
}

export function buildScheduleDuration(
  duration: ScheduleDuration | null,
): SingleScheduleDuration | MultipleScheduleDuration | null {
  if (!duration) return null
  function single_duration(value: number, worker: string, on: string): SingleScheduleDuration {
    return {
      single: true,
      value: value,
      worker: worker,
      on: on,
      minValue: null,
      maxValue: null,
      minWorkers: null,
      maxWorkers: null,
    }
  }

  function multipleDurations(
    minValue: number,
    maxValue: number,
    workers: Record<string, WorkerScheduleDuration>,
  ): MultipleScheduleDuration {
    const minWorkers = Object.values(workers).filter(function (item) {
      return item.value == minValue
    })
    const maxWorkers = Object.values(workers).filter(function (item) {
      return item.value == maxValue
    })
    return {
      single: false,
      minValue: minValue * 1000,
      maxValue: maxValue * 1000,
      minWorkers: minWorkers,
      maxWorkers: maxWorkers,
    }
  }

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
  const minValue = duration.workers[minWorker.worker_name || 'default'].value
  const maxValue = duration.workers[maxWorker.worker_name || 'default'].value
  return multipleDurations(minValue, maxValue, duration.workers)
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
