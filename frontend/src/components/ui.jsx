import { useTranslation } from '../i18n';

export function Badge({ tone = 'neutral', children }) {
  return <span className={`badge ${tone}`}>{children}</span>;
}

export function SectionShell({ title, description, eyebrow, actions, children, id, featured = false }) {
  return (
    <section id={id} className={`section-shell ${featured ? 'featured' : ''}`}>
      <div className="section-head">
        <div>
          {eyebrow ? <p className="section-eyebrow">{eyebrow}</p> : null}
          <h2>{title}</h2>
          {description ? <p className="section-description">{description}</p> : null}
        </div>
        {actions ? <div className="section-actions">{actions}</div> : null}
      </div>
      {children}
    </section>
  );
}

export function LoadingState({ label }) {
  return (
    <div className="loading-state" aria-live="polite" role="status">
      <span className="loading-dots" aria-hidden="true">
        <i />
        <i />
        <i />
      </span>
      <span className="loading-label">{label}</span>
      <span className="loading-skeleton" aria-hidden="true">
        <i />
        <i />
      </span>
    </div>
  );
}

export function FeedbackMessage({ tone = 'neutral', children }) {
  return (
    <div className={`feedback-message ${tone}`} role={tone === 'warning' ? 'alert' : 'status'}>
      {children}
    </div>
  );
}

export function EmptyState({ title, children }) {
  const { t } = useTranslation();

  return (
    <div className="empty-state-card" role="status">
      <strong>{title || t('common.empty.defaultTitle')}</strong>
      <p className="empty-state">{children}</p>
    </div>
  );
}
