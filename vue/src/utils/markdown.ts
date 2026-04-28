import { marked } from 'marked'

marked.setOptions({ breaks: true })

const renderer = new marked.Renderer()
const baseLink = renderer.link.bind(renderer)
renderer.link = (...args: Parameters<typeof baseLink>) => {
  const html = baseLink(...args)
  return html.replace(/^<a /, '<a target="_blank" rel="noopener noreferrer" ')
}

export function renderMarkdown(text: string): string {
  const normalized = text.replace(/([^\n])\n([-=]{2,})\n/g, '$1\n\n$2\n\n')
  return marked.parse(normalized, { renderer }) as string
}
