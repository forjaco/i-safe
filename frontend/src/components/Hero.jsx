import { useTranslation } from '../i18n';

export function Hero({ mode }) {
  const { t } = useTranslation();

  return (
    <section className="hero">
      <div className="hero-copy">
        <p className="section-eyebrow">{t('hero.eyebrow')}</p>
        <h1>{t('hero.title')}</h1>
        <p className="hero-text">{t('hero.text')}</p>
      </div>

      <div className="hero-summary">
        <div className="summary-row">
          <span>{t('hero.summary.focus.label')}</span>
          <strong>{t('hero.summary.focus.value')}</strong>
        </div>
        <div className="summary-row">
          <span>{t('hero.summary.reading.label')}</span>
          <strong>{mode === 'expert' ? t('hero.summary.reading.expert') : t('hero.summary.reading.beginner')}</strong>
        </div>
        <div className="summary-row">
          <span>{t('hero.summary.operation.label')}</span>
          <strong>{t('hero.summary.operation.value')}</strong>
        </div>
      </div>
    </section>
  );
}
