import type { TagItem } from '../types'
import { getPinyinInitials } from './pinyinInitial'

export function matchTags(
  query: string,
  allTags: TagItem[],
  recentTagIds: number[],
  limit = 8,
): TagItem[] {
  const q = query.toLowerCase()
  const textMatched = new Set<number>()
  const textResults: TagItem[] = []
  const pinyinResults: TagItem[] = []

  for (const tag of allTags) {
    if (tag.name.toLowerCase().includes(q)) {
      textResults.push(tag)
      textMatched.add(tag.id)
    }
  }

  if (q && /^[a-z]+$/.test(q)) {
    for (const tag of allTags) {
      if (!textMatched.has(tag.id)) {
        const initials = getPinyinInitials(tag.name)
        if (initials.includes(q)) pinyinResults.push(tag)
      }
    }
  }

  return [
    ...sortByRecent(textResults, recentTagIds),
    ...sortByRecent(pinyinResults, recentTagIds),
  ].slice(0, limit)
}

function sortByRecent(tags: TagItem[], recentTagIds: number[]): TagItem[] {
  return tags.sort((a, b) => {
    const ai = recentTagIds.indexOf(a.id)
    const bi = recentTagIds.indexOf(b.id)
    if (ai !== -1 && bi !== -1) return ai - bi
    if (ai !== -1) return -1
    if (bi !== -1) return 1
    return a.name.localeCompare(b.name)
  })
}

export const MAX_RECENT_TAGS = 10

export function pushRecentTag(recentTagIds: number[], tagId: number): number[] {
  const next = recentTagIds.filter(id => id !== tagId)
  next.unshift(tagId)
  return next.slice(0, MAX_RECENT_TAGS)
}
