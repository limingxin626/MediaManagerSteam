declare module 'plyr' {
  export default class Plyr {
    constructor(target: HTMLElement | string, options?: Plyr.Options)
    
    play(): Promise<void>
    pause(): void
    togglePlay(): void
    stop(): void
    restart(): void
    rewind(time: number): void
    forward(time: number): void
    increaseVolume(step?: number): void
    decreaseVolume(step?: number): void
    toggleCaptions(): void
    toggleControls(force?: boolean): void
    toggleFullscreen(): void
    toggleLoop(): void
    toggleMute(): void
    togglePIP(): void
    
    destroy(): void
    
    on(event: string, callback: Function): void
    once(event: string, callback: Function): void
    off(event: string, callback: Function): void
    
    get elements(): any
    get media(): HTMLVideoElement | HTMLAudioElement
    get playing(): boolean
    get paused(): boolean
    get stopped(): boolean
    get ended(): boolean
    get currentTime(): number
    set currentTime(time: number)
    get duration(): number
    get volume(): number
    set volume(volume: number)
    get muted(): boolean
    set muted(muted: boolean)
    get hasAudio(): boolean
    get speed(): number
    set speed(speed: number)
    get quality(): number
    set quality(quality: number)
    get loop(): boolean
    set loop(loop: boolean)
    get source(): string
    set source(source: string)
    get poster(): string
    set poster(poster: string)
    get autoplay(): boolean
    get captions(): any
    get fullscreen(): any
    get pip(): any
    get airplay(): any
  }
  
  namespace Plyr {
    interface Options {
      autoplay?: boolean
      captions?: {
        active?: boolean
        language?: string
        update?: boolean
      }
      controls?: string[]
      clickToPlay?: boolean
      disableContextMenu?: boolean
      displayDuration?: boolean
      fullscreen?: {
        enabled?: boolean
        fallback?: boolean
        iosNative?: boolean
      }
      hideControls?: boolean
      i18n?: any
      keyboard?: {
        focused?: boolean
        global?: boolean
      }
      listeners?: any
      loadSprite?: boolean
      loop?: {
        active?: boolean
      }
      muted?: boolean
      pip?: {
        enabled?: boolean
      }
      poster?: string
      quality?: {
        default?: number
        options?: number[]
        forced?: boolean
        onChange?: (quality: number) => void
      }
      ratio?: string
      seekTime?: number
      settings?: string[]
      speed?: {
        selected?: number
        options?: number[]
      }
      sources?: any[]
      spriteUrl?: string
      storage?: {
        enabled?: boolean
        key?: string
      }
      title?: string
      tooltips?: {
        controls?: boolean
        seek?: boolean
      }
      url?: string
      video?: {
        disablePictureInPicture?: boolean
      }
      volume?: number
    }
  }
}
