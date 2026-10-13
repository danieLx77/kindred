import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { BrandMark } from '../components/BrandMark'
import { useDocumentTitle } from '../hooks/useDocumentTitle'
import { paths } from '../routes'

export function HomePage() {
  const { t } = useTranslation()
  useDocumentTitle(t('home.title'))

  return (
    <section className="hero" aria-labelledby="home-heading">
      <div className="hero__content">
        <h1 id="home-heading">{t('home.heading')}</h1>
        <p className="lead">{t('home.lead')}</p>
        <Link className="button" to={paths.explore}>
          {t('home.cta')}
        </Link>
      </div>
      <div className="hero__art" aria-hidden="true">
        <BrandMark />
      </div>
    </section>
  )
}
