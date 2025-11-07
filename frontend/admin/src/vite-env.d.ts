/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_REALTIME_URL: string
  readonly VITE_FILES_URL: string
  readonly VITE_APP_NAME: string
  readonly VITE_APP_VERSION: string
  readonly VITE_ENVIRONMENT: string
  readonly VITE_JWT_STORAGE_KEY: string
  readonly VITE_REFRESH_TOKEN_KEY: string
  readonly VITE_SESSION_TIMEOUT_MINUTES: string
  readonly VITE_THEME: string
  readonly VITE_DEFAULT_LOCALE: string
  readonly VITE_SUPPORTED_LOCALES: string
  readonly VITE_ENABLE_ANALYTICS: string
  readonly VITE_ENABLE_REALTIME: string
  readonly VITE_ENABLE_NOTIFICATIONS: string
  readonly VITE_ENABLE_DARK_MODE: string
  readonly VITE_DASHBOARD_REFRESH_INTERVAL: string
  readonly VITE_KPI_REFRESH_INTERVAL: string
  readonly VITE_CHART_ANIMATION_DURATION: string
  readonly VITE_DEFAULT_PAGE_SIZE: string
  readonly VITE_MAX_PAGE_SIZE: string
  readonly VITE_MAX_FILE_SIZE_MB: string
  readonly VITE_ALLOWED_FILE_TYPES: string
  readonly VITE_DEBUG: string
  readonly VITE_LOG_LEVEL: string
  readonly VITE_MOCK_API: string
  readonly VITE_ENABLE_PWA: string
  readonly VITE_ENABLE_SERVICE_WORKER: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}