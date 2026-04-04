declare global {
  interface Window {
    electronAPI?: {
      openFileDialog: (options: { properties: string[] }) => Promise<{
        canceled: boolean
        filePaths: string[]
      }>
    }
  }
}

export {}
