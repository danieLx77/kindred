import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { useDocumentTitle } from '../hooks/useDocumentTitle'
import { paths } from '../routes'

export function NotFoundPage() {
  const { t } = useTranslation()
  useDocumentTitle(t('notFound.title'))

  return (
    <section className="page" aria-labelledby="not-found-heading">
      <h1 id="not-found-heading">{t('notFound.heading')}</h1>
      <p className="lead">{t('notFound.message')}</p>
      <Link className="button" to={paths.home}>
        {t('notFound.backHome')}
      </Link>
    </section>
  )
}
