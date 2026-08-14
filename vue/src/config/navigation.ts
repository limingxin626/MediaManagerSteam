export interface NavigationItem {
  path: string
  label: string
  icon: string
  mobile?: boolean
}

export const navigationItems: NavigationItem[] = [
  { path: '/', label: '主页', mobile: true, icon: 'M3 11.5 12 4l9 7.5M5.5 10v9h4.25v-5.5h4.5V19h4.25v-9' },
  { path: '/messages', label: '消息', mobile: true, icon: 'M5 5.5h14v11H9l-4 3v-14Z' },
  { path: '/media', label: '媒体', mobile: true, icon: 'M4 5h11v14H4zM15 9l5-3v12l-5-3' },
  { path: '/collection', label: '合集', mobile: true, icon: 'M4 7h16v12H4zM7 4h10M7 10h10' },
  { path: '/people', label: '人物', mobile: true, icon: 'M9 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Zm6 1a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM3 20v-2a5 5 0 0 1 10 0v2m2-6a4.5 4.5 0 0 1 6 4.25V20' },
  { path: '/transactions', label: '记账', icon: 'M12 3v18m4-14.5c-.8-1-2.1-1.5-4-1.5-2.2 0-4 1.2-4 3s1.8 3 4 3 4 1.2 4 3-1.8 3-4 3c-1.9 0-3.2-.5-4-1.5' },
  { path: '/admin', label: '管理', icon: 'M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Zm0-5 1 2.1 2.3.5 1.8-1.5 2.3 2.3-1.5 1.8.5 2.3 2.1 1v3.2l-2.1 1-.5 2.3 1.5 1.8-2.3 2.3-1.8-1.5-2.3.5-1 2.1H10l-1-2.1-2.3-.5-1.8 1.5-2.3-2.3 1.5-1.8-.5-2.3-2.1-1v-3.2l2.1-1 .5-2.3-1.5-1.8 2.3-2.3 1.8 1.5 2.3-.5 1-2.1Z' }
]

export function isNavigationActive(currentPath: string, itemPath: string) {
  return itemPath === '/' ? currentPath === '/' : currentPath.startsWith(itemPath)
}
