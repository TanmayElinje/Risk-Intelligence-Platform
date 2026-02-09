const StatsCards = ({ stats }) => {
  if (!stats) return null;

  const cards = [
    {
      title: 'Total Stocks',
      value: stats.total_stocks,
      icon: '📈',
      color: 'blue',
    },
    {
      title: 'High Risk',
      value: stats.high_risk_stocks,
      icon: '🚨',
      color: 'red',
    },
    {
      title: 'Avg Risk Score',
      value: stats.avg_risk_score?.toFixed(3),
      icon: '⚖️',
      color: 'yellow',
    },
    {
      title: 'Active Alerts',
      value: stats.total_alerts,
      icon: '🔔',
      color: 'orange',
    },
  ];

  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    red: 'bg-red-50 text-red-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    orange: 'bg-orange-50 text-orange-600',
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {cards.map((card) => (
        <div key={card.title} className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">{card.title}</p>
              <p className="text-3xl font-bold mt-1">{card.value}</p>
            </div>
            <div className={`text-4xl p-3 rounded-lg ${colorClasses[card.color]}`}>
              {card.icon}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default StatsCards;