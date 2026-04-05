import { Badge } from './ui';
import { useTranslation } from '../i18n';

export function TopBar({ currentUser, mode, language, onChangeLanguage, onToggleMode, onPrimaryAction }) {
  const { t } = useTranslation();

  return (
    <header className="topbar">
      <div className="brand-lockup">
        <div className="logo-mark" aria-hidden="true">
          I
        </div>
        <div>
          <p className="brand-kicker">I-safe</p>
          <strong className="brand-title">{t('topbar.title')}</strong>
        </div>
      </div>

      <div className="topbar-actions">
        <Badge tone={currentUser ? 'safe' : 'neutral'}>
          {currentUser ? t('common.status.authenticated') : t('common.status.local')}
        </Badge>

        <label className="language-select">
          <span>{t('topbar.language.label')}</span>
          <select value={language} onChange={(event) => onChangeLanguage(event.target.value)} aria-label={t('topbar.language.label')}>
            <option value="pt-BR">{t('common.language.pt')}</option>
            <option value="en">{t('common.language.en')}</option>
            <option value="es">{t('common.language.es')}</option>
          </select>
        </label>

        <button
          type="button"
          className="mode-toggle"
          onClick={onToggleMode}
          aria-pressed={mode === 'expert'}
        >
          {mode === 'expert' ? t('topbar.mode.expert') : t('topbar.mode.beginner')}
        </button>

        <button type="button" className="secondary-button" onClick={onPrimaryAction}>
          {currentUser ? t('common.action.logout') : t('common.action.enter')}
        </button>
      </div>
    </header>
  );
}
