declare global {
  interface Window {
    electronAPI?: {
      openFileDialog: (options: { properties: string[] }) => Promise<{
        canceled: boolean
        filePaths: string[]
      }>
      showItemInFolder: (path: string) => void
      setTitleBarTheme: (dark: boolean) => Promise<void>
    }
  }
}

export {}
