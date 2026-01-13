/**
 * Blob utilities for handling blob field types and kinds
 */

export const TEXT_KINDS = ['css', 'html', 'txt'] as const

export type BlobKind = 'image' | 'illustration' | 'css' | 'html' | 'txt'
export type TextKind = (typeof TEXT_KINDS)[number]

/**
 * Checks if a blob kind is a text type (css, html, txt)
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
