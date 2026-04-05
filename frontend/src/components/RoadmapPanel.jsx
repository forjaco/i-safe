import { SectionShell } from './ui';
import { useTranslation } from '../i18n';

export function RoadmapPanel() {
  const { t } = useTranslation();
  const roadmapItems = [
    { title: t('roadmap.vault'), label: t('roadmap.preview') },
    { title: t('roadmap.domainMonitoring'), label: t('roadmap.preview') },
    { title: t('roadmap.cleanup'), label: t('roadmap.soon') },
  ];

  return (
    <SectionShell
      id="roadmap"
      title={t('roadmap.title')}
      eyebrow={t('roadmap.eyebrow')}
      description={t('roadmap.description')}
    >
      <div className="roadmap-grid">
        {roadmapItems.map((item) => (
          <div key={item.title} className="roadmap-tile">
            <strong>{item.title}</strong>
            <span>{item.label}</span>
          </div>
        ))}
      </div>
    </SectionShell>
  );
}
