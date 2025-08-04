"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Wifi,
  WifiOff,
  Filter,
  Clock,
  DollarSign,
  Target,
  Zap,
  LogOut,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

interface Message {
  message_type: string;
  pair?: string;
  setup_type?: string;
  entry?: string;
  leverage?: string;
  tp1?: string;
  tp2?: string;
  tp3?: string;
  tp4?: string;
  timestamp?: string; // ISO string
  full_message?: string;
  sender?: string;
  text?: string;
}

type MessageType = "all" | "signal" | "market";
type TradeType = "all" | string; // e.g. "long", "short"
type TimeRange = "all" | number; // minutes

export default function Dashboard() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);

  const [filters, setFilters] = useState<{
    messageType: MessageType;
    pair: string | "all";
    tradeType: TradeType;
    timeRange: TimeRange;
  }>({
    messageType: "all",
    pair: "all",
    tradeType: "all",
    timeRange: "all",
  });

  // Handle scroll for header shadow
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Logout handler
  function handleLogout() {
    router.push("/login");
  }

  // Fetch historical messages with error handling
  useEffect(() => {
    async function fetchMessages() {
      try {
        const res = await fetch("/api/messages");
        const data = await res.json();
        if (Array.isArray(data)) {
          setMessages(data);
        } else if (data.error) {
          console.error("API error:", data.error);
          setMessages([]);
        } else {
          console.error("Unexpected API response:", data);
          setMessages([]);
        }
      } catch (err) {
        console.error("Fetch error:", err);
        setMessages([]);
      }
    }
    fetchMessages();
  }, []);

  // WebSocket live updates
  useEffect(() => {
    const ws = new WebSocket("wss://telegramsignals-production.up.railway.app");
    ws.onopen = () => setIsConnected(true);
    ws.onmessage = (event) => {
      try {
        const rawData = JSON.parse(event.data);
        console.log("Raw WebSocket message:", rawData);

        const newMsg: Message = {
          message_type: rawData.message_type || rawData.type || "market",
          pair: rawData.pair,
          setup_type: rawData.setup_type || rawData.setupType,
          entry: rawData.entry,
          leverage: rawData.leverage,
          tp1: rawData.tp1,
          tp2: rawData.tp2,
          tp3: rawData.tp3,
          tp4: rawData.tp4,
          timestamp: rawData.timestamp || new Date().toISOString(),
          full_message: rawData.full_message || rawData.fullMessage || rawData.message,
          sender: rawData.sender || rawData.from,
          text: rawData.text || rawData.content || rawData.message,
        };

        setMessages((prev) => [newMsg, ...prev]);
      } catch (error) {
        console.error("Error processing WebSocket message:", error, event.data);
      }
    };
    ws.onclose = () => setIsConnected(false);
    return () => ws.close();
  }, []);

  // Unique pairs for filter dropdown
  const uniquePairs = Array.from(new Set(messages.map((m) => m.pair).filter(Boolean))) as string[];

  // Filter messages (lowercase comparison)
  const filteredMessages = Array.isArray(messages)
      ? messages.filter((msg) => {
        const msgType = msg.message_type?.toLowerCase() ?? "";
        const setupType = msg.setup_type?.toLowerCase() ?? "";
        const pair = msg.pair ?? "";

        if (filters.messageType !== "all" && msgType !== filters.messageType) return false;
        if (filters.pair !== "all" && pair !== filters.pair) return false;
        if (filters.tradeType !== "all" && msgType === "signal" && setupType !== filters.tradeType) return false;
        if (filters.timeRange !== "all" && msg.timestamp) {
          const msgTime = new Date(msg.timestamp).getTime();
          const now = Date.now();
          if (msgTime < now - filters.timeRange * 60 * 1000) return false;
        }
        return true;
      })
      : [];

  const formatTime = (timestamp?: string) => {
    if (!timestamp) return "";
    return new Date(timestamp).toLocaleTimeString("en-US", {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getTimeAgo = (timestamp?: string) => {
    if (!timestamp) return "";
    const now = Date.now();
    const msgTime = new Date(timestamp).getTime();
    const diffMinutes = Math.floor((now - msgTime) / 60000);

    if (diffMinutes < 1) return "Just now";
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    const diffHours = Math.floor(diffMinutes / 60);
    return `${diffHours}h ago`;
  };

  return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 pb-10">
        {/* Header - Sticky with scroll effect */}
        <header className={`backdrop-blur-xl bg-white/5 border-b border-white/10 sticky top-0 z-50 transition-all duration-300 ${isScrolled ? "py-2" : "py-4"}`}>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 py-1">
            <div className="flex items-center justify-between">
              {/* Left side: title etc */}
              <div className="flex items-center space-x-2 md:space-x-4">
                <div className="flex items-center space-x-2 md:space-x-3">
                  <div className="w-8 h-8 md:w-10 md:h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
                    <Activity className="w-4 h-4 md:w-6 md:h-6 text-white" />
                  </div>
                  <div>
                    <h1 className="text-lg md:text-xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                      Live Dashboard
                    </h1>
                    <p className="text-xs md:text-sm text-gray-400">Real-time trading signals</p>
                  </div>
                </div>
              </div>

              {/* Right side: status, filters, logout */}
              <div className="flex items-center space-x-2 md:space-x-4">
                <div
                    className={`hidden sm:flex items-center space-x-1 px-2 py-1 md:px-3 md:py-1.5 rounded-full text-xs md:text-sm font-medium ${
                        isConnected
                            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                            : "bg-red-500/20 text-red-400 border border-red-500/30"
                    }`}
                >
                  {isConnected ? <Wifi className="w-3 h-3 md:w-4 md:h-4" /> : <WifiOff className="w-3 h-3 md:w-4 md:h-4" />}
                  <span className="hidden md:inline">{isConnected ? "Connected" : "Disconnected"}</span>
                </div>

                <button
                    onClick={() => setShowFilters(!showFilters)}
                    className="flex items-center space-x-1 px-3 py-1.5 md:px-4 md:py-2 bg-white/10 hover:bg-white/20 rounded-xl transition-all duration-200 text-white border border-white/20 text-sm"
                >
                  <Filter className="w-3 h-3 md:w-4 md:h-4" />
                  <span className="hidden sm:inline">Filters</span>
                </button>

                {/* Logout button - icon only on mobile */}
                <button
                    onClick={handleLogout}
                    className="flex items-center justify-center p-2 md:p-2 md:px-4 md:py-2 bg-purple-700 hover:bg-purple-800 rounded-xl transition-colors duration-200 text-white border border-purple-800"
                    title="Logout"
                >
                  <LogOut className="w-4 h-4 md:w-4 md:h-4" />
                  <span className="hidden md:inline ml-2">Logout</span>
                </button>
              </div>
            </div>
          </div>
        </header>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 md:py-6">
          {/* Connection status for mobile */}
          <div className="sm:hidden mb-4 flex justify-center">
            <div
                className={`flex items-center space-x-2 px-3 py-1.5 rounded-full text-sm font-medium ${
                    isConnected
                        ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                        : "bg-red-500/20 text-red-400 border border-red-500/30"
                }`}
            >
              {isConnected ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
              <span>{isConnected ? "Connected" : "Disconnected"}</span>
            </div>
          </div>

          {/* Filters Panel */}
          {showFilters && (
              <div className="p-4 md:p-6 bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 mb-6 animate-in slide-in-from-top duration-300">
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
                  {/* Message Type */}
                  <div>
                    <label className="block text-xs md:text-sm font-medium text-gray-300 mb-1 md:mb-2">Type</label>
                    <select
                        value={filters.messageType}
                        onChange={(e) => setFilters((f) => ({ ...f, messageType: e.target.value as MessageType }))}
                        className="w-full p-2 md:p-3 text-sm md:text-base bg-slate-800 rounded-xl border border-slate-600 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                      <option value="all" className="bg-slate-800 text-white">All</option>
                      <option value="signal" className="bg-slate-800 text-white">Signal</option>
                      <option value="market" className="bg-slate-800 text-white">Market</option>
                    </select>
                  </div>

                  {/* Pair */}
                  <div>
                    <label className="block text-xs md:text-sm font-medium text-gray-300 mb-1 md:mb-2">Pair</label>
                    <select
                        value={filters.pair}
                        onChange={(e) => setFilters((f) => ({ ...f, pair: e.target.value }))}
                        className="w-full p-2 md:p-3 text-sm md:text-base bg-slate-800 rounded-xl border border-slate-600 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                      <option value="all" className="bg-slate-800 text-white">All</option>
                      {uniquePairs.map((p) => (
                          <option key={p} value={p} className="bg-slate-800 text-white">{p}</option>
                      ))}
                    </select>
                  </div>

                  {/* Trade Type */}
                  <div>
                    <label className="block text-xs md:text-sm font-medium text-gray-300 mb-1 md:mb-2">Trade Type</label>
                    <select
                        value={filters.tradeType}
                        onChange={(e) => setFilters((f) => ({ ...f, tradeType: e.target.value }))}
                        className="w-full p-2 md:p-3 text-sm md:text-base bg-slate-800 rounded-xl border border-slate-600 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                      <option value="all" className="bg-slate-800 text-white">All</option>
                      <option value="long" className="bg-slate-800 text-white">Long</option>
                      <option value="short" className="bg-slate-800 text-white">Short</option>
                    </select>
                  </div>

                  {/* Time Range */}
                  <div>
                    <label className="block text-xs md:text-sm font-medium text-gray-300 mb-1 md:mb-2">Time Range</label>
                    <select
                        value={filters.timeRange}
                        onChange={(e) =>
                            setFilters((f) => ({
                              ...f,
                              timeRange: e.target.value === "all" ? "all" : parseInt(e.target.value),
                            }))
                        }
                        className="w-full p-2 md:p-3 text-sm md:text-base bg-slate-800 rounded-xl border border-slate-600 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                      <option value="all" className="bg-slate-800 text-white">All</option>
                      <option value="10" className="bg-slate-800 text-white">Last 10m</option>
                      <option value="30" className="bg-slate-800 text-white">Last 30m</option>
                      <option value="60" className="bg-slate-800 text-white">Last 1h</option>
                      <option value="240" className="bg-slate-800 text-white">Last 4h</option>
                    </select>
                  </div>
                </div>
              </div>
          )}

          {/* Messages */}
          <div className="space-y-3 md:space-y-4">
            {filteredMessages.length === 0 && (
                <div className="text-center py-8 md:py-12">
                  <Activity className="w-12 h-12 md:w-16 md:h-16 text-gray-500 mx-auto mb-3 md:mb-4 opacity-50" />
                  <p className="text-gray-400 text-base md:text-lg">No messages match your filter criteria</p>
                  <p className="text-gray-500 text-xs md:text-sm mt-1 md:mt-2">Try adjusting your filters or wait for new messages</p>
                </div>
            )}

            {filteredMessages.map((msg, idx) => {
              const msgType = msg.message_type?.toLowerCase();
              const isLong = msg.setup_type?.toLowerCase() === "long";

              return (
                  <div key={idx} className="group hover:scale-[1.01] md:hover:scale-[1.02] transition-all duration-300 active:scale-[0.99]">
                    {msgType === "signal" ? (
                        <div
                            className={`backdrop-blur-xl bg-gradient-to-r p-4 md:p-6 rounded-2xl border shadow-lg ${
                                isLong
                                    ? "from-emerald-500/10 to-green-500/5 border-emerald-500/30"
                                    : "from-red-500/10 to-pink-500/5 border-red-500/30"
                            }`}
                        >
                          {/* Debug info - remove this in production */}
                          {process.env.NODE_ENV === 'development' && (
                              <div className="text-xs text-gray-500 mb-1 md:mb-2 font-mono">
                                Debug: type="{msg.message_type}" setup="{msg.setup_type}" pair="{msg.pair}"
                              </div>
                          )}

                          <div className="flex items-start justify-between mb-3 md:mb-4">
                            <div className="flex items-center space-x-2 md:space-x-3">
                              <div
                                  className={`p-1.5 md:p-2 rounded-xl ${isLong ? "bg-emerald-500/20" : "bg-red-500/20"}`}
                              >
                                {isLong ? (
                                    <TrendingUp className="w-5 h-5 md:w-6 md:h-6 text-emerald-400" />
                                ) : (
                                    <TrendingDown className="w-5 h-5 md:w-6 md:h-6 text-red-400" />
                                )}
                              </div>
                              <div>
                                <h3 className="text-lg md:text-xl font-bold text-white">
                                  {msg.pair || "Unknown Pair"}{" "}
                                  <span
                                      className={`ml-1 md:ml-2 px-1.5 py-0.5 md:px-2 md:py-1 rounded-lg text-xs font-medium ${
                                          isLong ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"
                                      }`}
                                  >
                              {msg.setup_type?.toUpperCase() || "UNKNOWN"}
                            </span>
                                </h3>
                                <div className="flex items-center space-x-2 md:space-x-4 mt-1 text-xs md:text-sm text-gray-400">
                            <span className="flex items-center space-x-1">
                              <Clock className="w-3 h-3" />
                              <span>{formatTime(msg.timestamp)}</span>
                            </span>
                                  <span>{getTimeAgo(msg.timestamp)}</span>
                                </div>
                              </div>
                            </div>
                          </div>

                          <div className="grid grid-cols-2 md:grid-cols-3 gap-2 md:gap-4 mb-3 md:mb-4">
                            <div className="bg-white/5 rounded-xl p-2 md:p-4 border border-white/10">
                              <div className="flex items-center space-x-1 md:space-x-2 mb-1 md:mb-2">
                                <DollarSign className="w-3 h-3 md:w-4 md:h-4 text-purple-400" />
                                <span className="text-xs md:text-sm font-medium text-purple-400">Entry</span>
                              </div>
                              <p className="text-lg md:text-xl font-bold text-white">{msg.entry || "N/A"}</p>
                            </div>

                            <div className="bg-white/5 rounded-xl p-2 md:p-4 border border-white/10">
                              <div className="flex items-center space-x-1 md:space-x-2 mb-1 md:mb-2">
                                <Zap className="w-3 h-3 md:w-4 md:h-4 text-yellow-400" />
                                <span className="text-xs md:text-sm font-medium text-yellow-400">Leverage</span>
                              </div>
                              <p className="text-lg md:text-xl font-bold text-white">{msg.leverage || "N/A"}</p>
                            </div>

                            <div className="col-span-2 md:col-span-1 bg-white/5 rounded-xl p-2 md:p-4 border border-white/10">
                              <div className="flex items-center space-x-1 md:space-x-2 mb-1 md:mb-2">
                                <Target className="w-3 h-3 md:w-4 md:h-4 text-blue-400" />
                                <span className="text-xs md:text-sm font-medium text-blue-400">Take Profits</span>
                              </div>
                              <div className="grid grid-cols-2 gap-1 md:gap-2 text-xs md:text-sm">
                          <span className="text-gray-300">
                            TP1: <span className="text-white font-medium">{msg.tp1 || "N/A"}</span>
                          </span>
                                <span className="text-gray-300">
                            TP2: <span className="text-white font-medium">{msg.tp2 || "N/A"}</span>
                          </span>
                                <span className="text-gray-300">
                            TP3: <span className="text-white font-medium">{msg.tp3 || "N/A"}</span>
                          </span>
                                <span className="text-gray-300">
                            TP4: <span className="text-white font-medium">{msg.tp4 || "N/A"}</span>
                          </span>
                              </div>
                            </div>
                          </div>

                          {msg.full_message && (
                              <details className="bg-white/5 rounded-xl border border-white/10">
                                <summary className="p-3 cursor-pointer text-xs md:text-sm font-medium text-gray-300 hover:text-white transition-colors flex items-center justify-between">
                                  <span>View Full Message</span>
                                  <ChevronDown className="open:hidden w-4 h-4" />
                                  <ChevronUp className="hidden open:block w-4 h-4" />
                                </summary>
                                <div className="px-3 pb-3">
                          <pre className="text-xs md:text-sm text-gray-300 whitespace-pre-wrap font-mono bg-black/20 p-2 md:p-3 rounded-lg overflow-x-auto">
                            {msg.full_message}
                          </pre>
                                </div>
                              </details>
                          )}
                        </div>
                    ) : (
                        <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-4 md:p-6 shadow-lg">
                          {/* Debug info - remove this in production */}
                          {process.env.NODE_ENV === 'development' && (
                              <div className="text-xs text-gray-500 mb-1 md:mb-2 font-mono">
                                Debug: type="{msg.message_type}" sender="{msg.sender}"
                              </div>
                          )}

                          <div className="flex items-start space-x-3 md:space-x-4">
                            <div className="p-1.5 md:p-2 bg-blue-500/20 rounded-xl">
                              <Activity className="w-4 h-4 md:w-5 md:h-5 text-blue-400" />
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center justify-between mb-1 md:mb-2">
                                <h3 className="font-semibold text-white text-sm md:text-base">
                                  Market Update {msg.sender && `from ${msg.sender}`}
                                </h3>
                                <div className="flex items-center space-x-2 md:space-x-4 text-xs text-gray-400">
                            <span className="flex items-center space-x-1">
                              <Clock className="w-2 h-2 md:w-3 md:h-3" />
                              <span>{formatTime(msg.timestamp)}</span>
                            </span>
                                  <span>{getTimeAgo(msg.timestamp)}</span>
                                </div>
                              </div>
                              <p className="text-gray-300 leading-relaxed text-sm md:text-base">{msg.text}</p>
                            </div>
                          </div>
                        </div>
                    )}
                  </div>
              );
            })}
          </div>
        </div>
      </div>
  );
}