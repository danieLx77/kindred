import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { I18nextProvider } from 'react-i18next'
import { BrowserRouter } from 'react-router-dom'
import '@fontsource-variable/figtree/wght.css'
import '@fontsource/young-serif/400.css'
import './index.css'
import App from './App.tsx'
import { createI18n } from './i18n/index.ts'

const i18n = createI18n()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <I18nextProvider i18n={i18n}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </I18nextProvider>
  </StrictMode>,
)
