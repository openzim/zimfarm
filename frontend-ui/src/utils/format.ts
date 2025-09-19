import { filesize } from 'filesize'
import { DateTime, Duration, Interval, type DurationUnit } from 'luxon'

function getUnits(interval: Interval<true>) {
  const units: string[] = []
  const allUnits = ['months', 'days', 'hours', 'minutes']
  allUnits.forEach(function (unit) {
    if (interval.length(unit as DurationUnit) >= 1) units.push(unit)
  })
  if (units.length == 0) units.push('seconds')
  return units
}

function toDurationObj(milliseconds: number) {
  const items: Record<string, number> = {
    years: 0,
    months: 0,
    days: 0,
    hours: 0,
    minutes: 0,
    seconds: 0,
    milliseconds: milliseconds,
  }

  function toObj() {
    const o: Record<string, number> = {}
    Object.entries(items).forEach((item) => {
      const [key, value] = item
      if (value >= 1 && key != 'milliseconds') o[key] = value
    })
    return o
  }

  function shift(lower: string, upper: string, num: number) {
    items[upper] = items[lower] / num
    items[lower] = items[lower] % num
    return items[upper] < 1
  }
  if (shift('milliseconds', 'seconds', 1000)) return toObj()
  if (shift('seconds', 'minutes', 60)) return toObj()
  if (shift('minutes', 'hours', 60)) return toObj()
  if (shift('hours', 'days', 24)) return toObj()
  if (shift('days', 'months', 30)) return toObj()
  shift('months', 'years', 12)
  return toObj()
}

export function formatDuration(value: number) {
  const dur = Duration.fromObject(toDurationObj(value))
  return dur.toHuman({ maximumSignificantDigits: 1 })
}

export function formatDt(value?: string, format: string = 'fff') {
  // display a datetime in the provided format (defaults to 'fff')
  if (!value) return ''
  const dt = DateTime.fromISO(value)
  if (!dt.isValid) return value
  return dt.toFormat(format)
}

export function formatDurationBetween(start: string, end: string) {
  // display a duration between two datetimes
  const interval = Interval.fromDateTimes(DateTime.fromISO(start), DateTime.fromISO(end))
  const diff = Duration.fromObject(
    interval.toDuration(getUnits(interval as Interval<true>) as DurationUnit[]).toObject(),
  )
  return diff.toHuman({ maximumSignificantDigits: 1 })
}

export function fromNow(value: string) {
  if (!value) return ''
  const start = DateTime.fromISO(value)
  if (!start.isValid) return value
  return start.toRelative()
}

export function formattedBytesSize(value: number) {
  return filesize(value, { base: 2, standard: 'iec', precision: 3 }) // display in KiB, MiB,... instead of KB, MB,...
}

export function getTimezoneDetails() {
  const dt = DateTime.local()
  const diff = Duration.fromObject({ minutes: Math.abs(dt.offset) })
  let offsetstr = ''
  let amount = ''
  if (diff.minutes % 60 == 0) {
    amount = `${diff.as('hour')} hour`
    if (diff.minutes > 60) amount += 's'
  } else amount = `${diff.toHuman({ unitDisplay: 'long' })}`

  if (dt.offset > 0) offsetstr = `${amount} ahead of UTC`
  else if (dt.offset < 0) offsetstr = `${amount} behind UTC`
  else offsetstr = 'in par with UTC'
  return { tz: dt.zoneName, offset: dt.offset, offsetstr: offsetstr }
}
