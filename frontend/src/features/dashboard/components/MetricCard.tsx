/**
 * Metric Card.
 *
 * Clickable stat card with icon, value, label, trend indicator,
 * and supporting text. Used for the core hierarchy:
 * Providers → Databases → Tables → Columns.
 */

import { useNavigate } from 'react-router-dom';
import { TrendingUp } from 'lucide-react';

interface MetricCardProps {
  icon: React.ReactNode;
  value: number;
  label: string;
  subtitle: string;
  trend?: string;
  navigateTo: string;
  delay?: number;
}

export default function MetricCard({
  icon,
  value,
  label,
  subtitle,
  trend,
  navigateTo,
  delay = 0,
}: MetricCardProps) {
  const navigate = useNavigate();

  const formattedValue = value >= 1000
    ? value.toLocaleString()
    : String(value);

  return (
    <div
      className="metric-card animate-fade-in"
      role="button"
      tabIndex={0}
      onClick={() => navigate(navigateTo)}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') navigate(navigateTo); }}
      style={{ animationDelay: `${delay}s`, opacity: 0 }}
    >
      <div className="metric-card__header">
        <div className="metric-card__icon">
          {icon}
        </div>
        {trend && (
          <div className="metric-card__trend">
            <TrendingUp size={11} />
            {trend}
          </div>
        )}
      </div>
      <div className="metric-card__value">{formattedValue}</div>
      <div className="metric-card__label">{label}</div>
      <div className="metric-card__sub">{subtitle}</div>
    </div>
  );
}
