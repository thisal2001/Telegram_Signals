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
  RefreshCw,
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
  stop_loss?: string;
  timestamp?: string;
  full_message?: string;
  sender?: string;
  text?: string;
}

type MessageType = "all" | "signal" | "market";
type TradeType = "all" | string;
type TimeRange = "all" | number;

export default function Dashboard() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [isFetching, setIsFetching] = useState(false);
  const [toast, setToast] = useState({
    visible: false,
    message: "",
    type: "success" as "success" | "error",
  });

  const [filters, setFilters] = useState({
    messageType: "all" as MessageType,
    pair: "all",
    tradeType: "all" as TradeType,
    timeRange: "all" as TimeRange,
  });

  // Handle logout
  const handleLogout = () => {
    router.push("/login");
  };

  // Fetch initial messages
  useEffect(() => {
    const fetchMessages = async () => {
      try {
        const res = await fetch("/api/messages");
        const data = await res.json();
        if (Array.isArray(data)) {
          setMessages(data);
        }
      } catch (err) {
        console.error("Fetch error:", err);
      }
    };
    fetchMessages();
  }, []);

  // WebSocket connection
  useEffect(() => {
    const ws = new WebSocket("wss://telegramsignals-production.up.railway.app/ws");

    ws.onopen = () => setIsConnected(true);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const newMsg: Message = {
          message_type: data.type || "market",
          ...data,
        };
        setMessages((prev) => [newMsg, ...prev]);
      } catch (error) {
        console.error("WebSocket error:", error);
      }
    };
    ws.onclose = () => setIsConnected(false);

    return () => ws.close();
  }, []);

  // Fetch past messages
  const handleFetchPastMessages = async () => {
    try {
      setIsFetching(true);

      const response = await fetch("https://telegramsignals-production.up.railway.app/fetch-past", {
        method: "GET",
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Fetch failed: ${response.status} ${errorText}`);
      }

      const data = await response.json();
      console.log("Fetch response:", data);

      showToast("Messages fetched successfully!", "success");
      window.location.reload();
    } catch (error) {
      console.error("Fetch error:", error);
      showToast(`Failed to fetch messages: ${error}`, "error");
    } finally {
      setIsFetching(false);
    }
  };

  // Show toast notification
  const showToast = (message: string, type: "success" | "error") => {
    setToast({ visible: true, message, type });
    setTimeout(() => {
      setToast((prev) => ({ ...prev, visible: false }));
    }, 3000);
  };

  // Filter messages
  const uniquePairs = Array.from(
      new Set(messages.map((m) => m.pair).filter(Boolean))
  ) as string[];

  const filteredMessages = messages.filter((msg) => {
    const msgType = msg.message_type?.toLowerCase() ?? "";
    const setupType = msg.setup_type?.toLowerCase() ?? "";
    const pair = msg.pair ?? "";

    if (filters.messageType !== "all" && msgType !== filters.messageType) return false;
    if (filters.pair !== "all" && pair !== filters.pair) return false;
    if (filters.tradeType !== "all" && msgType === "signal" && setupType !== filters.tradeType) return false;
    if (filters.timeRange !== "all" && msg.timestamp) {
      const msgTime = new Date(msg.timestamp).getTime();
      const now = Date.now();
      if (msgTime < now - (filters.timeRange as number) * 60 * 1000) return false;
    }
    return true;
  });

  // Format time helpers
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
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        {/* ...rest of your JSX remains unchanged... */}
        {/* Buttons, filters panel, messages rendering, toast */}
      </div>
  );
}
