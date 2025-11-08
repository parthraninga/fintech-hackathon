import React from 'react';

interface ChartData {
  month: string;
  revenue: number;
}

interface RevenueChartProps {
  data: ChartData[];
  formatCurrency: (amount: number) => string;
}

const RevenueChart: React.FC<RevenueChartProps> = ({ data, formatCurrency }) => {
  if (!data || data.length === 0) {
    return (
      <div className="no-data">
        No revenue data available
      </div>
    );
  }

  const maxRevenue = Math.max(...data.map(d => d.revenue));
  const minRevenue = Math.min(...data.map(d => d.revenue));
  const revenueRange = maxRevenue - minRevenue;

  // Calculate height percentage for each bar
  const getBarHeight = (revenue: number) => {
    if (revenueRange === 0) return 50; // Default height if all values are the same
    return Math.max(20, ((revenue - minRevenue) / revenueRange) * 80 + 20);
  };

  // Get color based on revenue performance
  const getBarColor = (revenue: number) => {
    const performance = revenue / maxRevenue;
    if (performance >= 0.8) return '#4caf50'; // Green for high performance
    if (performance >= 0.6) return '#2196f3'; // Blue for good performance
    if (performance >= 0.4) return '#ff9800'; // Orange for medium performance
    return '#f44336'; // Red for low performance
  };

  return (
    <div className="chart-container">
      <div className="chart-bars">
        {data.slice(-6).map((item, index) => {
          const barHeight = getBarHeight(item.revenue);
          const barColor = getBarColor(item.revenue);
          
          return (
            <div key={`${item.month}-${index}`} className="chart-bar">
              <div 
                className="bar-fill"
                style={{ 
                  height: `${barHeight}%`,
                  background: `linear-gradient(135deg, ${barColor} 0%, ${barColor}dd 100%)`,
                  boxShadow: `0 2px 8px ${barColor}33`
                }}
                title={`${item.month}: ${formatCurrency(item.revenue)}`}
              >
                <div className="bar-tooltip">
                  {formatCurrency(item.revenue)}
                </div>
              </div>
              <div className="bar-label">{item.month}</div>
              <div className="bar-value">{formatCurrency(item.revenue)}</div>
            </div>
          );
        })}
      </div>
      
      {/* Chart Y-axis labels */}
      <div className="chart-y-axis">
        <div className="y-axis-label y-axis-max">
          {formatCurrency(maxRevenue)}
        </div>
        <div className="y-axis-label y-axis-mid">
          {formatCurrency((maxRevenue + minRevenue) / 2)}
        </div>
        <div className="y-axis-label y-axis-min">
          {formatCurrency(minRevenue)}
        </div>
      </div>
    </div>
  );
};

export default RevenueChart;