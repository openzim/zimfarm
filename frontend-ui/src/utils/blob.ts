/**
 * Blob utilities for handling blob field types and kinds
 */

export const TEXT_KINDS = ['css', 'html', 'js', 'txt'] as const

export type BlobKind = 'image' | 'illustration' | 'css' | 'html' | 'js' | 'txt'
export type TextKind = (typeof TEXT_KINDS)[number]

/**
 * Checks if a blob kind is a text type (css, html, js, txt)
 */
export const isTextKind = (kind: BlobKind): kind is TextKind => {
  return TEXT_KINDS.includes(kind as TextKind)
}

/**
 * Checks if a blob kind is an image type
 */
export const isImageKind = (kind: BlobKind): boolean => {
  return kind === 'image' || kind === 'illustration'
}

export const textToBase64 = (text: string): string => {
  const utf8Bytes = new TextEncoder().encode(text)
  let binaryString = ''
  for (let i = 0; i < utf8Bytes.length; i++) {
    binaryString += String.fromCharCode(utf8Bytes[i])
  }
  return btoa(binaryString)
}
