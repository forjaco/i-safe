import { Badge, FeedbackMessage, SectionShell } from './ui';
import { useTranslation } from '../i18n';

export function AuthPanel({
  authLoading,
  authMessage,
  authTone,
  currentUser,
  loginForm,
  onLoginSubmit,
  onLogout,
  onRefresh,
  onLoginFormChange,
}) {
  const { t } = useTranslation();

  return (
    <SectionShell
      id="session"
      title={t('auth.section.title')}
      eyebrow={t('auth.section.eyebrow')}
      description={t('auth.section.description')}
    >
      {currentUser ? (
        <div className="session-panel">
          <div className="session-card">
            <div>
              <p className="micro-label">{t('auth.accountActive')}</p>
              <strong>{currentUser.email}</strong>
            </div>
            <Badge tone="safe">ID {currentUser.id}</Badge>
          </div>

          <div className="session-actions">
            <button type="button" onClick={onRefresh} disabled={authLoading}>
              {authLoading ? t('auth.refresh.loading') : t('auth.refresh')}
            </button>
            <button type="button" className="secondary-button" onClick={onLogout} disabled={authLoading}>{t('common.action.logout')}</button>
          </div>
        </div>
      ) : (
        <form className="form-grid" onSubmit={onLoginSubmit}>
          <div className="auth-access-card">
            <div>
              <p className="micro-label">{t('auth.demo.title')}</p>
              <strong>demo@isafe.local</strong>
            </div>
            <code>DemoPass123!</code>
          </div>

          <label className="field">
            <span>{t('auth.email.label')}</span>
            <input
              type="email"
              value={loginForm.email}
              onChange={(event) => onLoginFormChange('email', event.target.value)}
              placeholder={t('auth.email.placeholder')}
              autoComplete="email"
              required
            />
          </label>

          <label className="field">
            <span>{t('auth.password.label')}</span>
            <input
              type="password"
              value={loginForm.password}
              onChange={(event) => onLoginFormChange('password', event.target.value)}
              placeholder={t('auth.password.placeholder')}
              autoComplete="current-password"
              required
            />
          </label>

          <p className="auth-note">{t('auth.note.cookie')}</p>

          <p className="auth-note">{t('auth.note.provisioned')}</p>

          <button type="submit" disabled={authLoading}>
            {authLoading ? t('auth.login.loading') : t('auth.login.submit')}
          </button>
        </form>
      )}

      {authMessage ? <FeedbackMessage tone={authTone}>{authMessage}</FeedbackMessage> : null}
    </SectionShell>
  );
}
