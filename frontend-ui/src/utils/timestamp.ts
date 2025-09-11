/**
 * Default timestamp for when no timestamp is found
 */
export const DEFAULT_TIMESTAMP = new Date('1970-01-01T00:00:00.000Z')

export function getTimestampForStatus(
  timestampList: [string, string][],
  status: string,
  defaultTimestamp: Date = DEFAULT_TIMESTAMP,
): Date {
  // Filter timestamps for the given status
  const matchingTimestamps = timestampList
    .filter(([statusStr]) => statusStr === status)
    .map(([, timestamp]) => new Date(timestamp))

  if (matchingTimestamps.length === 0) {
    return defaultTimestamp
  }

  // Return the most recent timestamp for this status
  return new Date(Math.max(...matchingTimestamps.map((d) => d.getTime())))
}

export function getTimestampStringForStatus(
  timestampList: [string, string][],
  status: string,
  defaultTimestamp: string = DEFAULT_TIMESTAMP.toISOString(),
): string {
  // Filter timestamps for the given status
  const matchingTimestamps = timestampList
    .filter(([statusStr]) => statusStr === status)
    .map(([, timestamp]) => timestamp)

  if (matchingTimestamps.length === 0) {
    return defaultTimestamp
  }

  // Return the most recent timestamp string for this status
  // Sort by timestamp string (ISO format) and return the latest
  return matchingTimestamps.sort().pop()!
}
