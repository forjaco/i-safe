import { EmptyState, FeedbackMessage, LoadingState, SectionShell } from './ui';
import {
  translateAction,
  translateDataType,
  translateExposureLevel,
  translateLookupStatus,
  translateRecommendation,
  useTranslation,
} from '../i18n';

function getRiskBadge(riskScore, t) {
  const total = riskScore?.pontuacao_total ?? 0;
  if (total >= 100) {
    return { label: t('osint.risk.critical'), tone: 'danger' };
  }
  if (total > 0) {
    return { label: t('osint.risk.warning'), tone: 'warning' };
  }
  return { label: t('osint.risk.safe'), tone: 'safe' };
}

function getLookupSummary(result, t) {
  if (result?.status === 'RESTRICTED') {
    return t('osint.result.summary.restricted');
  }

  if (result?.status === 'MOCK_SUCCESS') {
    return t('osint.result.summary.mock');
  }

  if (result?.is_leaked) {
    return t('osint.result.summary.leaked');
  }

  return t('osint.result.summary.clean');
}

function LookupResult({
  result,
  loading,
  expertMode,
  emptySitesBody,
  emptyDataBody,
}) {
  const { t } = useTranslation();
  const riskBadge = getRiskBadge(result?.risk_score, t);
  const recommendations = (result.recommendations || []).map((item) => translateRecommendation(item));
  const translatedAction = translateAction(result.action);

  return (
    <div className={`result-shell ${loading ? 'is-updating' : ''}`}>
      <div className="result-hero">
        <div>
          <p className="micro-label">{t('osint.result.title')}</p>
          <h3>{result.status === 'RESTRICTED' ? t('osint.result.restricted') : t('osint.result.normal')}</h3>
          <p className="result-copy">{getLookupSummary(result, t)}</p>
        </div>
        <div className={`score-panel ${riskBadge.tone}`}>
          <span className="micro-label">{t('osint.result.score')}</span>
          <strong>{result.risk_score?.pontuacao_total ?? 0}</strong>
          <span>{riskBadge.label}</span>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-tile">
          <span>{t('osint.result.status')}</span>
          <strong>{translateLookupStatus(result.status)}</strong>
        </div>
        <div className="stat-tile">
          <span>{t('osint.result.exposure')}</span>
          <strong>{result.is_leaked ? t('osint.result.exposure.detected') : t('osint.result.exposure.notDetected')}</strong>
        </div>
        <div className="stat-tile">
          <span>{t('osint.result.level')}</span>
          <strong>{translateExposureLevel(result.risk_score?.nivel_exposicao)}</strong>
        </div>
      </div>

      {!expertMode ? <p className="result-summary">{translatedAction}</p> : null}

      <div className="content-grid">
        <div className="info-block">
          <h4>{t('osint.result.relatedSources')}</h4>
          {result.sites?.length ? (
            <ul className="plain-list">
              {result.sites.map((site) => (
                <li key={site}>{site}</li>
              ))}
            </ul>
          ) : (
            <EmptyState title={t('osint.result.emptySources.title')}>{emptySitesBody}</EmptyState>
          )}
        </div>

        <div className="info-block">
          <h4>{t('osint.result.exposedData')}</h4>
          {result.leaked_data_types?.length ? (
            <ul className="chip-row">
              {result.leaked_data_types.map((item) => (
                <li key={item}>{translateDataType(item)}</li>
              ))}
            </ul>
          ) : (
            <EmptyState title={t('osint.result.emptyData.title')}>{emptyDataBody}</EmptyState>
          )}
        </div>
      </div>

      <div className="info-block">
        <h4>{expertMode ? t('osint.result.recommendations') : t('osint.result.nextSteps')}</h4>
        {recommendations.length ? (
          <ul className="recommendation-list">
            {recommendations.map((item) => (
              <li key={`${item.title}-${item.priority}`}>
                <div className="recommendation-head">
                  <strong>{item.title}</strong>
                  <span>{item.priority}</span>
                </div>
                <p>{item.description}</p>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState title={t('osint.result.emptyRecommendations.title')}>
            {t('osint.result.emptyRecommendations.body')}
          </EmptyState>
        )}
      </div>

      <div className="action-strip">
        <span className="micro-label">{t('osint.result.action')}</span>
        <strong>{translatedAction}</strong>
      </div>

      {expertMode ? (
        <details className="expert-panel">
          <summary>{t('osint.result.technicalDetails')}</summary>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </details>
      ) : null}
    </div>
  );
}

export function OsintPanel({
  email,
  expertMode,
  loading,
  error,
  result,
  phone,
  phoneLoading,
  phoneError,
  phoneResult,
  onEmailChange,
  onSubmit,
  onPhoneChange,
  onPhoneSubmit,
}) {
  const { t } = useTranslation();

  return (
    <SectionShell
      id="email-check"
      title={t('osint.section.title')}
      eyebrow={t('osint.section.eyebrow')}
      featured
      description={t('osint.section.description')}
    >
      <div className="lookup-stack">
        <div className="lookup-card lookup-card-primary">
          <div className="lookup-intro">
            <p className="micro-label">{t('osint.primary.label')}</p>
            <h3>{t('osint.primary.title')}</h3>
            <p className="lookup-copy">{t('osint.primary.description')}</p>
          </div>

          <form className="form-grid hero-form" onSubmit={onSubmit}>
            <label className="field field-large">
              <span>{t('osint.email.label')}</span>
              <input
                type="email"
                value={email}
                onChange={(event) => onEmailChange(event.target.value)}
                placeholder={t('auth.email.placeholder')}
                required
              />
              <small className="field-hint">{t('osint.email.hint')}</small>
            </label>

            <button type="submit" className="primary-button" disabled={loading}>
              {loading ? t('osint.email.loading') : t('osint.email.submit')}
            </button>
          </form>

          {loading ? <LoadingState label={t('osint.loading')} /> : null}
          {error ? <FeedbackMessage tone="warning">{error}</FeedbackMessage> : null}
          {!result && !loading && !error ? (
            <EmptyState title={t('osint.email.empty.title')}>{t('osint.email.empty.body')}</EmptyState>
          ) : null}

          {result ? (
            <LookupResult
              result={result}
              loading={loading}
              expertMode={expertMode}
              emptySitesBody={t('osint.result.emptySources.email')}
              emptyDataBody={t('osint.result.emptyData.email')}
            />
          ) : null}
        </div>

        <div className="lookup-card lookup-card-secondary">
          <div className="lookup-intro">
            <div className="lookup-heading-row">
              <div>
                <p className="micro-label">{t('osint.phone.labelBlock')}</p>
                <h3>{t('osint.phone.title')}</h3>
              </div>
              <span className="inline-badge">{t('osint.phone.featureFlag')}</span>
            </div>
            <p className="lookup-copy">{t('osint.phone.description')}</p>
          </div>

          <form className="form-grid hero-form secondary-form" onSubmit={onPhoneSubmit}>
            <label className="field">
              <span>{t('osint.phone.label')}</span>
              <input
                type="tel"
                value={phone}
                onChange={(event) => onPhoneChange(event.target.value)}
                placeholder={t('osint.phone.placeholder')}
                inputMode="tel"
                required
              />
              <small className="field-hint">{t('osint.phone.hint')}</small>
            </label>

            <button type="submit" className="secondary-button" disabled={phoneLoading}>
              {phoneLoading ? t('osint.phone.loading') : t('osint.phone.submit')}
            </button>
          </form>

          {phoneLoading ? <LoadingState label={t('osint.phone.loadingState')} /> : null}
          {phoneError ? <FeedbackMessage tone="warning">{phoneError}</FeedbackMessage> : null}
          {!phoneResult && !phoneLoading && !phoneError ? (
            <EmptyState title={t('osint.phone.empty.title')}>{t('osint.phone.empty.body')}</EmptyState>
          ) : null}

          {phoneResult ? (
            <LookupResult
              result={phoneResult}
              loading={phoneLoading}
              expertMode={expertMode}
              emptySitesBody={t('osint.result.emptySources.phone')}
              emptyDataBody={t('osint.result.emptyData.phone')}
            />
          ) : null}
        </div>
      </div>
    </SectionShell>
  );
}
