/**
 * Computes the SHA-256 checksum of a base64-encoded data string
 */
export async function computeChecksumFromBase64(base64Data: string): Promise<string> {
  const base64Content = base64Data.includes(',') ? base64Data.split(',')[1] : base64Data

  const binaryString = atob(base64Content)

  // Convert binary string to Uint8Array
  const bytes = new Uint8Array(binaryString.length)
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i)
  }

  const hashBuffer = await crypto.subtle.digest('SHA-256', bytes)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  const hashHex = hashArray.map((b) => b.toString(16).padStart(2, '0')).join('')

  return hashHex
}

/**
 * Computes the SHA-256 checksum of a File object
 */
export async function computeChecksumFromFile(file: File): Promise<string> {
  const arrayBuffer = await file.arrayBuffer()
  const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer)

  // Convert hash to hex string
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  const hashHex = hashArray.map((b) => b.toString(16).padStart(2, '0')).join('')

  return hashHex
}
