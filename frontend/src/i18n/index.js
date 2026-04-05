import { useEffect, useState } from 'react';
import pt from './pt.json';
import en from './en.json';
import es from './es.json';

const LANGUAGE_STORAGE_KEY = 'isafe.language';
const DEFAULT_LANGUAGE = 'pt-BR';
const SUPPORTED_LANGUAGES = {
  'pt-BR': pt,
  en,
  es,
};

const listeners = new Set();

let currentLanguage = detectInitialLanguage();

function detectInitialLanguage() {
  if (typeof window === 'undefined') {
    return DEFAULT_LANGUAGE;
  }

  const storedLanguage = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
  if (storedLanguage && SUPPORTED_LANGUAGES[storedLanguage]) {
    return storedLanguage;
  }

  const browserLanguage = window.navigator.language || DEFAULT_LANGUAGE;
  if (browserLanguage.toLowerCase().startsWith('pt')) {
    return 'pt-BR';
  }
  if (browserLanguage.toLowerCase().startsWith('es')) {
    return 'es';
  }
  if (browserLanguage.toLowerCase().startsWith('en')) {
    return 'en';
  }

  return DEFAULT_LANGUAGE;
}

function resolveMessage(language, key) {
  return SUPPORTED_LANGUAGES[language]?.[key] ?? SUPPORTED_LANGUAGES[DEFAULT_LANGUAGE]?.[key] ?? key;
}

function interpolate(message, params = {}) {
  return Object.entries(params).reduce(
    (current, [paramKey, value]) => current.replaceAll(`{${paramKey}}`, String(value)),
    message,
  );
}

export function getCurrentLanguage() {
  return currentLanguage;
}

export function setLanguage(nextLanguage) {
  const safeLanguage = SUPPORTED_LANGUAGES[nextLanguage] ? nextLanguage : DEFAULT_LANGUAGE;
  currentLanguage = safeLanguage;

  if (typeof window !== 'undefined') {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, safeLanguage);
    document.documentElement.lang = safeLanguage;
  }

  listeners.forEach((listener) => listener(safeLanguage));
}

export function subscribeToLanguage(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function t(key, params = {}, language = currentLanguage) {
  return interpolate(resolveMessage(language, key), params);
}

const BACKEND_DETAIL_MAP = {
  'Credenciais inválidas.': 'backend.detail.invalidCredentials',
  'Access token inválido.': 'backend.detail.invalidAccessToken',
  'Refresh token inválido.': 'backend.detail.invalidRefreshToken',
  'Sessão inválida. Faça login novamente.': 'backend.detail.invalidSession',
  'Entrada inválida para a consulta.': 'backend.detail.invalidInput',
  'Serviço indisponível no momento.': 'backend.detail.serviceUnavailable',
  'O arquivo enviado está vazio.': 'backend.detail.emptyFile',
  'Não foi possível validar o arquivo de imagem com segurança.': 'backend.detail.invalidImage',
  'Mimetype não aceito. Apenas JPG e PNG são permitidos.': 'backend.detail.invalidMime',
  'O conteúdo do arquivo não corresponde ao mimetype informado.': 'backend.detail.invalidContentType',
  'A imagem enviada é inválida.': 'backend.detail.invalidImageData',
  'A imagem excede o limite seguro de resolução.': 'backend.detail.imageTooManyPixels',
  'Payload excede o limite de segurança permitido.': 'backend.detail.payloadTooLarge',
};

const BACKEND_ACTION_MAP = {
  '[✔] DADOS CRIPTOGRAFADOS E ENGAVETADOS NO AEGIS.DB (MODO MOCK)': 'backend.action.email.mock',
  '[✔] DADOS CRIPTOGRAFADOS E ENGAVETADOS NO AEGIS.DB': 'backend.action.email.success',
  '[!] RESPOSTA RESTRITA PARA PROTEÇÃO CONTRA ABUSO': 'backend.action.restricted',
  '[!] CONSULTA DE TELEFONE EM MODO MOCK CONTROLADO': 'backend.action.phone.mock',
};

const RECOMMENDATION_TITLE_MAP = {
  'Rotacione credenciais reutilizadas': 'backend.recommendation.rotate.title',
  'Fortaleça o canal de recuperação de contas': 'backend.recommendation.recovery.title',
  'Reduza risco de clonagem e vishing': 'backend.recommendation.phone.title',
  'Mantenha monitoramento contínuo': 'backend.recommendation.monitor.title',
  'Aguarde antes de tentar novamente': 'backend.recommendation.restricted.title',
};

const RECOMMENDATION_DESCRIPTION_MAP = {
  'Troque senhas expostas, priorize e-mail principal e habilite 2FA por aplicativo autenticador.': 'backend.recommendation.rotate.description',
  'Revise filtros anti-phishing, aliases públicos e métodos de recuperação vinculados ao e-mail monitorado.': 'backend.recommendation.recovery.description',
  'Ative PIN da operadora e verificação em duas etapas em mensageria para dificultar engenharia social.': 'backend.recommendation.phone.description',
  'Continue monitorando o e-mail e revise periodicamente senhas, 2FA e exposição pública de dados.': 'backend.recommendation.monitor.description',
  'Continue monitorando o identificador consultado e revise periodicamente senhas, 2FA e exposição pública de dados.': 'backend.recommendation.monitor.description',
  'A consulta foi processada em modo restrito para proteger o serviço contra abuso.': 'backend.recommendation.restricted.description',
};

const PRIORITY_MAP = {
  high: 'backend.priority.high',
  medium: 'backend.priority.medium',
  low: 'backend.priority.low',
};

const EXPOSURE_LEVEL_MAP = {
  baixo: 'backend.exposureLevel.low',
  médio: 'backend.exposureLevel.medium',
  medio: 'backend.exposureLevel.medium',
  crítico: 'backend.exposureLevel.critical',
  critico: 'backend.exposureLevel.critical',
  'indisponível': 'backend.exposureLevel.unavailable',
  indisponivel: 'backend.exposureLevel.unavailable',
};

const DATA_TYPE_MAP = {
  email: 'backend.dataType.email',
  password: 'backend.dataType.password',
  phone: 'backend.dataType.phone',
  telefone: 'backend.dataType.phone',
  name: 'backend.dataType.name',
  nome: 'backend.dataType.name',
};

const PRIVACY_ALERT_MAP = {
  "ALERTA DE PRIVACIDADE CRÍTICO: Esta imagem contém metadados de localização embutidos (Coordenadas GPS ativas). Cibercriminosos podem extrair a latitude e longitude exatas de onde esta foto foi tirada. Recomendamos que limpe ou desabilite a marcação de fotos com localização no seu aplicativo de câmera nativo.": 'backend.privacyAlert.gps',
};

export function translateBackendDetail(detail, language = currentLanguage) {
  if (!detail) {
    return detail;
  }

  if (BACKEND_DETAIL_MAP[detail]) {
    return t(BACKEND_DETAIL_MAP[detail], {}, language);
  }

  const largeFileMatch = detail.match(/^O arquivo excede o limite de segurança de (\d+)MB\.$/);
  if (largeFileMatch) {
    return t('backend.detail.imageTooLarge', { limit: largeFileMatch[1] }, language);
  }

  return detail;
}

export function translateLookupStatus(status, language = currentLanguage) {
  return t(`backend.status.${status}`, {}, language);
}

export function translateExposureLevel(level, language = currentLanguage) {
  const key = EXPOSURE_LEVEL_MAP[String(level || '').trim().toLowerCase()];
  return key ? t(key, {}, language) : level;
}

export function translateAction(action, language = currentLanguage) {
  const key = BACKEND_ACTION_MAP[action];
  return key ? t(key, {}, language) : action;
}

export function translateRecommendation(item, language = currentLanguage) {
  return {
    ...item,
    title: RECOMMENDATION_TITLE_MAP[item.title] ? t(RECOMMENDATION_TITLE_MAP[item.title], {}, language) : item.title,
    description: RECOMMENDATION_DESCRIPTION_MAP[item.description]
      ? t(RECOMMENDATION_DESCRIPTION_MAP[item.description], {}, language)
      : item.description,
    priority: PRIORITY_MAP[item.priority] ? t(PRIORITY_MAP[item.priority], {}, language) : item.priority,
  };
}

export function translateDataType(value, language = currentLanguage) {
  const key = DATA_TYPE_MAP[String(value || '').trim().toLowerCase()];
  return key ? t(key, {}, language) : value;
}

export function translatePrivacyAlert(alert, language = currentLanguage) {
  const key = PRIVACY_ALERT_MAP[alert];
  return key ? t(key, {}, language) : alert;
}

export function useTranslation() {
  const [language, setLanguageState] = useState(getCurrentLanguage());

  useEffect(() => {
    document.documentElement.lang = language;
    return subscribeToLanguage(setLanguageState);
  }, [language]);

  return {
    language,
    setLanguage,
    t: (key, params = {}) => t(key, params, language),
  };
}
