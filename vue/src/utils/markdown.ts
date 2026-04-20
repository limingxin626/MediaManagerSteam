import { marked } from 'marked'

marked.setOptions({ breaks: true })

export function renderMarkdown(text: string): string {
  const normalized = text.replace(/([^\n])\n([-=]{2,})\n/g, '$1\n\n$2\n\n')
  return marked.parse(normalized) as string
}
