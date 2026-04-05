import { useMemo, useState } from 'react';
import { EmptyState, FeedbackMessage, LoadingState, SectionShell } from './ui';
import { translatePrivacyAlert, useTranslation } from '../i18n';

function getFileHint(file, t) {
  if (!file) {
    return t('upload.dropzone.hint');
  }
  return `${file.name} · ${file.type || t('common.value.unknownType')} · ${file.size} bytes`;
}

export function PrivacyPanel({
  loading,
  error,
  result,
  onSubmit,
  onFileSelect,
  mode,
}) {
  const { t } = useTranslation();
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState(null);
  const fileHint = useMemo(() => getFileHint(file, t), [file, t]);

  function handleSelection(nextFile) {
    setFile(nextFile || null);
    onFileSelect(nextFile || null);
  }

  function handleDrop(event) {
    event.preventDefault();
    setIsDragging(false);
    handleSelection(event.dataTransfer.files?.[0] || null);
  }

  return (
    <SectionShell
      id="privacy-upload"
      title={t('upload.section.title')}
      eyebrow={t('upload.section.eyebrow')}
      description={t('upload.section.description')}
    >
      <form className="upload-form" onSubmit={onSubmit}>
        <label
          className={`dropzone ${isDragging ? 'dragging' : ''}`}
          onDragOver={(event) => {
            event.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
        >
          <input
            type="file"
            accept="image/jpeg,image/png"
            onChange={(event) => handleSelection(event.target.files?.[0] || null)}
          />
          <p className="dropzone-kicker">{t('upload.dropzone.kicker')}</p>
          <strong>{t('upload.dropzone.title')}</strong>
          <span>{fileHint}</span>
        </label>

        <div className="button-row">
          <button type="submit" className="primary-button" disabled={loading}>
            {loading ? t('upload.submit.loading') : t('upload.submit')}
          </button>
          <button type="button" className="secondary-button" disabled>
            {t('upload.sanitize')}
          </button>
        </div>
      </form>

      {loading ? <LoadingState label={t('upload.loading')} /> : null}
      {error ? <FeedbackMessage tone="warning">{error}</FeedbackMessage> : null}
      {!result && !loading && !error ? (
        <EmptyState title={t('upload.empty.title')}>{t('upload.empty.body')}</EmptyState>
      ) : null}

      {result ? (
        <div className={`result-shell ${loading ? 'is-updating' : ''}`}>
          <div className="result-hero compact">
            <div>
              <p className="micro-label">{t('upload.result.file')}</p>
              <h3>{result.filename}</h3>
              <p className="result-copy">
                {result.is_safe ? t('upload.result.safe') : t('upload.result.warning')}
              </p>
            </div>
            <div className={`score-panel ${result.is_safe ? 'safe' : 'warning'}`}>
              <span className="micro-label">{t('upload.result.security')}</span>
              <strong>{result.is_safe ? t('upload.result.ok') : t('upload.result.attention')}</strong>
              <span>{result.metadata_found ? t('upload.result.metadataFound') : t('upload.result.noMetadata')}</span>
            </div>
          </div>

          <div className="stats-grid">
            <div className="stat-tile">
              <span>{t('upload.result.metadataField')}</span>
              <strong>{result.metadata_found ? t('common.value.yes') : t('common.value.no')}</strong>
            </div>
            <div className="stat-tile">
              <span>{t('upload.result.sanitization')}</span>
              <strong>{result.sanitization_available ? t('roadmap.soon') : t('upload.result.notNeeded')}</strong>
            </div>
            <div className="stat-tile">
              <span>{t('upload.result.size')}</span>
              <strong>{result.size_bytes}</strong>
            </div>
          </div>

          {mode !== 'expert' ? (
            <p className="result-summary">
              {result.is_safe ? t('upload.result.beginner.safe') : t('upload.result.beginner.warning')}
            </p>
          ) : null}

          <div className="info-block">
            <h4>{mode === 'expert' ? t('upload.result.alertsExpert') : t('upload.result.alerts')}</h4>
            {result.privacy_alerts?.length ? (
              <ul className="recommendation-list">
                {result.privacy_alerts.map((alert) => (
                  <li key={alert}>
                    <p>{translatePrivacyAlert(alert)}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState title={t('upload.result.emptyAlerts.title')}>{t('upload.result.emptyAlerts.body')}</EmptyState>
            )}
          </div>
        </div>
      ) : null}
    </SectionShell>
  );
}
