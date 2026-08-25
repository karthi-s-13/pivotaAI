/**
 * Dashboard Welcome.
 *
 * Time-of-day greeting with organization name and action buttons.
 */

import { useNavigate } from 'react-router-dom';
import { Plus, Map } from 'lucide-react';
import { getGreeting } from '../api/dashboardApi';

interface DashboardWelcomeProps {
  organizationName: string;
}

export default function DashboardWelcome({ organizationName }: DashboardWelcomeProps) {
  const navigate = useNavigate();
  const greeting = getGreeting();

  return (
    <div className="dashboard-welcome">
      <div className="dashboard-welcome__greeting">
        <h1>
          {greeting},{' '}
          <span className="gradient-text">{organizationName}</span>
        </h1>
        <p>Here's what's happening across your connected data environment.</p>
      </div>
      <div className="dashboard-welcome__actions">
        <button
          className="btn-primary"
          onClick={() => navigate('/data-sources')}
          style={{ fontSize: '0.8rem', padding: '9px 18px' }}
        >
          <Plus size={16} />
          Add Data Source
        </button>
        <button
          className="btn-ghost"
          onClick={() => navigate('/data-map')}
          style={{ fontSize: '0.8rem', padding: '9px 18px' }}
        >
          <Map size={16} />
          View Data Map
        </button>
      </div>
    </div>
  );
}
