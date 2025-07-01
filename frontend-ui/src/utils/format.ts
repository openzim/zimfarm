import { filesize } from 'filesize';
import { DateTime, Duration, Interval, type DurationUnit } from 'luxon';

function getUnits(interval: Interval<true>) {
  const units: string[] = [];
  const allUnits = ["months", "days", "hours", "minutes"];
  allUnits.forEach(function (unit) {
    if (interval.length(unit as DurationUnit) >= 1) units.push(unit);
  });
  if (units.length == 0) units.push("seconds");
  return units;
}


export function formatDt(value: string) {
  // display a datetime in a standard format
  if (!value) return "";
  const dt = DateTime.fromISO(value);
  if (!dt.isValid) return value;
  return dt.toFormat("fff");
}

export function formatDurationBetween(start: string, end: string) {
  // display a duration between two datetimes
  const interval = Interval.fromDateTimes(
    DateTime.fromISO(start),
    DateTime.fromISO(end)
  );
  const diff = Duration.fromObject(interval.toDuration(getUnits(interval as Interval<true>) as DurationUnit[]).toObject());
  return diff.toHuman({ maximumSignificantDigits: 1 });
}

export function fromNow(value: string) {
  if (!value) return "";
  const start = DateTime.fromISO(value);
  if (!start.isValid) return value;
  return start.toRelative();
}


export function formattedBytesSize(value: number) {
  if (!value) return "";
  return filesize(value, { base: 2, standard: "iec", precision: 3 }); // precision 3, display in KiB, MiB,... instead of KB, MB,...
}
