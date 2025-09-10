export function isFirefoxOnIOS() {
  const ua = navigator.userAgent.toLowerCase()
  return ua.indexOf('mobile') >= 0 && ua.indexOf('mozilla') >= 0 && ua.indexOf('applewebkit') >= 0
}

export function generatePassword(
  length = 12,
  chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789',
) {
  const array = new Uint8Array(length)
  crypto.getRandomValues(array)
  return Array.from(array, (x) => chars[x % chars.length]).join('')
}
