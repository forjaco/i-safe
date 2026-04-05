import { useEffect, useState } from 'react';
import { clearAccessToken, configureApiClient, getAccessToken, getAuthErrorMessage } from '../api/client';
import { fetchCurrentUser, getApiErrorMessage, login, logout, refreshSession } from '../api/services';
import { useTranslation } from '../i18n';

const initialLoginForm = {
  email: '',
  password: '',
};

export function useAuthSession() {
  const { t, language } = useTranslation();
  const [loginForm, setLoginForm] = useState(initialLoginForm);
  const [currentUser, setCurrentUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(false);
  const [authMessage, setAuthMessage] = useState('');
  const [authTone, setAuthTone] = useState('neutral');

  useEffect(() => {
    configureApiClient({
      onUnauthorized: () => {
        setCurrentUser(null);
        setAuthMessage(t('auth.session.expired'));
        setAuthTone('warning');
      },
    });
  }, [language]);

  useEffect(() => {
    let mounted = true;

    async function bootstrapSession() {
      try {
        const token = getAccessToken();
        if (!token) {
          const refreshData = await refreshSession();
          if (!refreshData?.access_token) {
            return;
          }
        }

        const me = await fetchCurrentUser();
        if (mounted) {
          setCurrentUser(me);
          setAuthMessage('');
          setAuthTone('neutral');
        }
      } catch (error) {
        clearAccessToken();
        if (mounted && !error?.response) {
          setAuthMessage(t('auth.bootstrap.error'));
          setAuthTone('warning');
        }
      }
    }

    bootstrapSession();

    return () => {
      mounted = false;
    };
  }, [language]);

  async function handleLogin(event) {
    event.preventDefault();
    setAuthLoading(true);
    setAuthMessage('');
    setAuthTone('neutral');

    try {
      await login(loginForm);
      const me = await fetchCurrentUser();
      setCurrentUser(me);
      setAuthMessage(t('auth.login.success'));
      setAuthTone('success');
      setLoginForm(initialLoginForm);
    } catch (error) {
      setAuthMessage(getAuthErrorMessage(error, 'auth.login.error.fallback'));
      setAuthTone('warning');
    } finally {
      setAuthLoading(false);
    }
  }

  async function handleLogout() {
    setAuthLoading(true);
    setAuthMessage('');
    setAuthTone('neutral');

    try {
      await logout();
      setCurrentUser(null);
      setAuthMessage(t('auth.logout.success'));
      setAuthTone('neutral');
    } catch (error) {
      setAuthMessage(getApiErrorMessage(error, 'auth.logout.error'));
      setAuthTone('warning');
    } finally {
      setAuthLoading(false);
    }
  }

  async function handleRefresh() {
    setAuthLoading(true);
    setAuthMessage('');
    setAuthTone('neutral');

    try {
      await refreshSession();
      const me = await fetchCurrentUser();
      setCurrentUser(me);
      setAuthMessage(t('auth.session.renewed'));
      setAuthTone('success');
    } catch (error) {
      setCurrentUser(null);
      setAuthMessage(t('auth.session.renewError'));
      setAuthTone('warning');
    } finally {
      setAuthLoading(false);
    }
  }

  return {
    authLoading,
    authMessage,
    authTone,
    currentUser,
    loginForm,
    setLoginForm,
    handleLogin,
    handleLogout,
    handleRefresh,
  };
}
