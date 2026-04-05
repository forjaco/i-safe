import { useState } from 'react';
import { getApiErrorMessage, checkEmailExposure, checkPhoneExposure, uploadPrivacyImage } from './api/services';
import { AuthPanel } from './components/AuthPanel';
import { Hero } from './components/Hero';
import { OsintPanel } from './components/OsintPanel';
import { PrivacyPanel } from './components/PrivacyPanel';
import { RoadmapPanel } from './components/RoadmapPanel';
import { TopBar } from './components/TopBar';
import { useAuthSession } from './hooks/useAuthSession';
import { useTranslation } from './i18n';

function scrollToSession() {
  const target = document.getElementById('session');
  target?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function App() {
  const { t, language, setLanguage } = useTranslation();
  const {
    authLoading,
    authMessage,
    authTone,
    currentUser,
    loginForm,
    setLoginForm,
    handleLogin,
    handleLogout,
    handleRefresh,
  } = useAuthSession();

  const [mode, setMode] = useState('beginner');
  const [email, setEmail] = useState('');
  const [osintLoading, setOsintLoading] = useState(false);
  const [osintError, setOsintError] = useState('');
  const [osintResult, setOsintResult] = useState(null);
  const [phone, setPhone] = useState('');
  const [phoneLoading, setPhoneLoading] = useState(false);
  const [phoneError, setPhoneError] = useState('');
  const [phoneResult, setPhoneResult] = useState(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [uploadResult, setUploadResult] = useState(null);

  const expertMode = mode === 'expert';

  function handleLoginFormChange(field, value) {
    setLoginForm((current) => ({ ...current, [field]: value }));
  }

  function handleToggleMode() {
    setMode((current) => (current === 'expert' ? 'beginner' : 'expert'));
  }

  async function handleOsintSubmit(event) {
    event.preventDefault();
    setOsintLoading(true);
    setOsintError('');

    try {
      const result = await checkEmailExposure(email);
      setOsintResult(result);
    } catch (error) {
      setOsintError(getApiErrorMessage(error, 'osint.email.error'));
    } finally {
      setOsintLoading(false);
    }
  }

  async function handleUploadSubmit(event) {
    event.preventDefault();
    setUploadLoading(true);
    setUploadError('');

    try {
      if (!selectedFile) {
        setUploadError(t('upload.error.missingFile'));
        return;
      }

      const result = await uploadPrivacyImage(selectedFile);
      setUploadResult(result);
    } catch (error) {
      setUploadError(getApiErrorMessage(error, 'upload.error.fallback'));
    } finally {
      setUploadLoading(false);
    }
  }

  async function handlePhoneSubmit(event) {
    event.preventDefault();
    setPhoneLoading(true);
    setPhoneError('');

    try {
      const result = await checkPhoneExposure(phone);
      setPhoneResult(result);
    } catch (error) {
      setPhoneError(getApiErrorMessage(error, 'osint.phone.error'));
    } finally {
      setPhoneLoading(false);
    }
  }

  return (
    <div className="page-shell">
      <TopBar
        currentUser={currentUser}
        mode={mode}
        language={language}
        onChangeLanguage={setLanguage}
        onToggleMode={handleToggleMode}
        onPrimaryAction={currentUser ? handleLogout : scrollToSession}
      />

      <main className="page-main">
        <Hero mode={mode} />

        <section className="trust-strip" aria-label={t('trust.product.label')}>
          <div className="trust-item">
            <span>{t('trust.product.label')}</span>
            <strong>{t('trust.product.value')}</strong>
          </div>
          <div className="trust-item">
            <span>{t('trust.usage.label')}</span>
            <strong>{t('trust.usage.value')}</strong>
          </div>
          <div className="trust-item">
            <span>{t('trust.backend.label')}</span>
            <strong>{t('trust.backend.value')}</strong>
          </div>
        </section>

        <section className="content-layout">
          <div className="content-main">
            <OsintPanel
              email={email}
              expertMode={expertMode}
              loading={osintLoading}
              error={osintError}
              result={osintResult}
              phone={phone}
              phoneLoading={phoneLoading}
              phoneError={phoneError}
              phoneResult={phoneResult}
              onEmailChange={setEmail}
              onSubmit={handleOsintSubmit}
              onPhoneChange={setPhone}
              onPhoneSubmit={handlePhoneSubmit}
            />

            <PrivacyPanel
              loading={uploadLoading}
              error={uploadError}
              result={uploadResult}
              onSubmit={handleUploadSubmit}
              onFileSelect={setSelectedFile}
              mode={mode}
            />
          </div>

          <aside className="content-side">
            <AuthPanel
              authLoading={authLoading}
              authMessage={authMessage}
              authTone={authTone}
              currentUser={currentUser}
              loginForm={loginForm}
              onLoginSubmit={handleLogin}
              onLogout={handleLogout}
              onRefresh={handleRefresh}
              onLoginFormChange={handleLoginFormChange}
            />

            <RoadmapPanel />
          </aside>
        </section>
      </main>
    </div>
  );
}

export default App;
