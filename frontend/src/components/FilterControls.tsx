import { Label } from "@/components/ui/label";

interface FilterControlsProps {
  filters: {
    timeRange: string;
    tradeType: string;
    pair: string;
    messageType: string;
  };
  onFiltersChange: (filters: any) => void;
  availablePairs: string[];
}

export function FilterControls({ filters, onFiltersChange, availablePairs }: FilterControlsProps) {
  const handleFilterChange = (key: string, value: string) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      {/* Time Range Filter */}
      <div className="space-y-2">
        <Label htmlFor="timeRange">Time Range</Label>
        <select
          id="timeRange"
          value={filters.timeRange}
          onChange={(e) => handleFilterChange("timeRange", e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Time</option>
          <option value="1h">Last Hour</option>
          <option value="24h">Last 24 Hours</option>
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
        </select>
      </div>

      {/* Trade Type Filter */}
      <div className="space-y-2">
        <Label htmlFor="tradeType">Trade Type</Label>
        <select
          id="tradeType"
          value={filters.tradeType}
          onChange={(e) => handleFilterChange("tradeType", e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Types</option>
          <option value="LONG">Long</option>
          <option value="SHORT">Short</option>
          <option value="SCALP">Scalp</option>
          <option value="SWING">Swing</option>
        </select>
      </div>

      {/* Trading Pair Filter */}
      <div className="space-y-2">
        <Label htmlFor="pair">Trading Pair</Label>
        <select
          id="pair"
          value={filters.pair}
          onChange={(e) => handleFilterChange("pair", e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Pairs</option>
          {availablePairs.map((pair) => (
            <option key={pair} value={pair}>
              {pair}
            </option>
          ))}
        </select>
      </div>

      {/* Message Type Filter */}
      <div className="space-y-2">
        <Label htmlFor="messageType">Message Type</Label>
        <select
          id="messageType"
          value={filters.messageType}
          onChange={(e) => handleFilterChange("messageType", e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Messages</option>
          <option value="signal">Trading Signals</option>
          <option value="market">Market Updates</option>
        </select>
      </div>
    </div>
  );
} 