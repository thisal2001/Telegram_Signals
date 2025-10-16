"use client"

import { useState, useEffect } from "react"
import { RefreshCw, TrendingUp, TrendingDown, DollarSign, Shield, Zap, Settings, ArrowLeft, Play, Target } from "lucide-react"

interface TradeExecution {
    id: string
    symbol: string
    side: "BUY" | "SELL"
    setupType: "LONG" | "SHORT"
    quantity: number
    avgPrice: number
    status: string
    timestamp: string
    leverage: number
    entry: number
    stopLoss: number
    tp1?: number
    tp2?: number
    tp3?: number
    tp4?: number
}

interface PositionInfo {
    symbol: string
    size: number
    entryPrice: number
    markPrice: number
    pnl: number
    pnlPercent: number
    margin: number
    leverage: number
    side: "LONG" | "SHORT"
}

interface AccountInfo {
    totalBalance: number
    availableBalance: number
    totalMargin: number
    totalPnl: number
    totalPnlPercent: number
}

export default function TradingDashboard() {
    const [executions, setExecutions] = useState<TradeExecution[]>([])
    const [positions, setPositions] = useState<PositionInfo[]>([])
    const [account, setAccount] = useState<AccountInfo | null>(null)
    const [isLoading, setIsLoading] = useState(false)
    const [activeTab, setActiveTab] = useState<"dashboard" | "config">("dashboard")
    const [positionSize, setPositionSize] = useState(1000)
    const [maxLeverage, setMaxLeverage] = useState(20)

    const [manualTrade, setManualTrade] = useState({
        symbol: "BTCUSDT",
        side: "LONG" as "LONG" | "SHORT",
        positionSize: 1000,
        leverage: 10,
        stopLoss: "",
        takeProfit1: "",
        takeProfit2: "",
        takeProfit3: "",
        takeProfit4: "",
    })

    useEffect(() => {
        setExecutions([
            {
                id: "1",
                symbol: "BTCUSDT",
                side: "BUY",
                setupType: "LONG",
                quantity: 0.5,
                avgPrice: 43250.5,
                status: "FILLED",
                timestamp: new Date().toISOString(),
                leverage: 10,
                entry: 43250.5,
                stopLoss: 42800.0,
                tp1: 43800.0,
                tp2: 44200.0,
                tp3: 44600.0,
                tp4: 45000.0,
            },
        ])

        setPositions([
            {
                symbol: "BTCUSDT",
                size: 0.5,
                entryPrice: 43250.5,
                markPrice: 43420.75,
                pnl: 85.13,
                pnlPercent: 3.94,
                margin: 2162.53,
                leverage: 10,
                side: "LONG",
            },
        ])

        setAccount({
            totalBalance: 5000.0,
            availableBalance: 2837.47,
            totalMargin: 2162.53,
            totalPnl: 85.13,
            totalPnlPercent: 1.7,
        })
    }, [])

    const refreshData = async () => {
        setIsLoading(true)
        await new Promise((resolve) => setTimeout(resolve, 1000))
        setIsLoading(false)
    }

    const savePositionConfig = () => {
        console.log("Saving position config:", { positionSize, maxLeverage })
    }

    const executeManualTrade = () => {
        console.log("Executing manual trade:", manualTrade)
        alert(`Manual trade executed: ${manualTrade.side} ${manualTrade.symbol} with ${manualTrade.leverage}x leverage`)
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
            {/* Header */}
            <header className="backdrop-blur-xl bg-white/5 border-b border-white/10 sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                            <button
                                onClick={() => window.history.back()}
                                className="p-2 hover:bg-white/10 rounded-xl transition-colors"
                            >
                                <ArrowLeft className="w-5 h-5 text-white" />
                            </button>
                            <div className="flex items-center space-x-3">
                                <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
                                    <DollarSign className="w-6 h-6 text-white" />
                                </div>
                                <div>
                                    <h1 className="text-xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                                        Trading Dashboard
                                    </h1>
                                    <p className="text-sm text-gray-400">Binance futures monitoring</p>
                                </div>
                            </div>
                        </div>

                        <button
                            onClick={refreshData}
                            disabled={isLoading}
                            className="flex items-center space-x-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-xl transition-all duration-200 text-white border border-white/20"
                        >
                            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
                            <span>Refresh</span>
                        </button>
                    </div>
                </div>
            </header>

            <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
                {/* Account Overview Cards */}
                {account && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                        <div className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-6 hover:scale-105 transition-transform duration-300">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-gray-300">Total Balance</span>
                                <DollarSign className="w-4 h-4 text-purple-400" />
                            </div>
                            <div className="text-2xl font-bold text-white">${account.totalBalance.toFixed(2)}</div>
                            <p className="text-xs text-gray-400 mt-1">USDT</p>
                        </div>

                        <div className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-6 hover:scale-105 transition-transform duration-300">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-gray-300">Available Balance</span>
                                <Zap className="w-4 h-4 text-yellow-400" />
                            </div>
                            <div className="text-2xl font-bold text-white">${account.availableBalance.toFixed(2)}</div>
                            <p className="text-xs text-gray-400 mt-1">Ready to trade</p>
                        </div>

                        <div className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-6 hover:scale-105 transition-transform duration-300">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-gray-300">Total Margin</span>
                                <Shield className="w-4 h-4 text-blue-400" />
                            </div>
                            <div className="text-2xl font-bold text-white">${account.totalMargin.toFixed(2)}</div>
                            <p className="text-xs text-gray-400 mt-1">In positions</p>
                        </div>

                        <div className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-6 hover:scale-105 transition-transform duration-300">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-gray-300">Total PnL</span>
                                {account.totalPnl >= 0 ? (
                                    <TrendingUp className="w-4 h-4 text-emerald-400" />
                                ) : (
                                    <TrendingDown className="w-4 h-4 text-red-400" />
                                )}
                            </div>
                            <div className={`text-2xl font-bold ${account.totalPnl >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                                ${account.totalPnl.toFixed(2)}
                            </div>
                            <p className={`text-xs mt-1 ${account.totalPnlPercent >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                                {account.totalPnlPercent >= 0 ? "+" : ""}{account.totalPnlPercent.toFixed(2)}%
                            </p>
                        </div>
                    </div>
                )}

                {/* Tabs */}
                <div className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-2 mb-6">
                    <div className="flex space-x-2">
                        <button
                            onClick={() => setActiveTab("dashboard")}
                            className={`flex-1 px-4 py-2 rounded-xl font-medium transition-all duration-200 ${
                                activeTab === "dashboard"
                                    ? "bg-purple-600 text-white"
                                    : "text-gray-300 hover:bg-white/10"
                            }`}
                        >
                            Dashboard
                        </button>
                        <button
                            onClick={() => setActiveTab("config")}
                            className={`flex-1 px-4 py-2 rounded-xl font-medium transition-all duration-200 ${
                                activeTab === "config"
                                    ? "bg-purple-600 text-white"
                                    : "text-gray-300 hover:bg-white/10"
                            }`}
                        >
                            Position Config
                        </button>
                    </div>
                </div>

                {/* Dashboard Tab */}
                {activeTab === "dashboard" && (
                    <div className="space-y-6">
                        {/* Trade Executions */}
                        <div className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-6">
                            <h2 className="text-xl font-bold text-white mb-2">Recent Trade Executions</h2>
                            <p className="text-sm text-gray-400 mb-6">Latest automated trade executions from signals</p>

                            <div className="space-y-4">
                                {executions.map((execution) => (
                                    <div key={execution.id} className="backdrop-blur-xl bg-gradient-to-r from-emerald-500/10 to-green-500/5 border border-emerald-500/30 rounded-2xl p-6">
                                        <div className="flex items-center justify-between mb-4">
                                            <div className="flex items-center space-x-3">
                                                <span className={`px-3 py-1 rounded-lg text-xs font-medium ${
                                                    execution.setupType === "LONG"
                                                        ? "bg-emerald-500/20 text-emerald-400"
                                                        : "bg-red-500/20 text-red-400"
                                                }`}>
                                                    {execution.setupType}
                                                </span>
                                                <span className="font-semibold text-white text-lg">{execution.symbol}</span>
                                                <span className="px-2 py-1 bg-white/10 rounded-lg text-xs text-gray-300">
                                                    {execution.leverage}x
                                                </span>
                                            </div>
                                            <div className="text-sm text-gray-400">
                                                {new Date(execution.timestamp).toLocaleString()}
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                                            <div className="bg-white/5 rounded-xl p-3 border border-white/10">
                                                <p className="text-xs text-gray-400 mb-1">Quantity</p>
                                                <p className="font-medium text-white">{execution.quantity}</p>
                                            </div>
                                            <div className="bg-white/5 rounded-xl p-3 border border-white/10">
                                                <p className="text-xs text-gray-400 mb-1">Avg Price</p>
                                                <p className="font-medium text-white">${execution.avgPrice.toFixed(2)}</p>
                                            </div>
                                            <div className="bg-white/5 rounded-xl p-3 border border-white/10">
                                                <p className="text-xs text-gray-400 mb-1">Stop Loss</p>
                                                <p className="font-medium text-red-400">${execution.stopLoss.toFixed(2)}</p>
                                            </div>
                                            <div className="bg-white/5 rounded-xl p-3 border border-white/10">
                                                <p className="text-xs text-gray-400 mb-1">Status</p>
                                                <span className="px-2 py-1 bg-emerald-500/20 text-emerald-400 rounded text-xs font-medium">
                                                    {execution.status}
                                                </span>
                                            </div>
                                        </div>

                                        <div className="bg-white/5 rounded-xl p-4 border border-white/10">
                                            <p className="text-sm text-gray-400 mb-3">Take Profit Targets</p>
                                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                                {execution.tp1 && (
                                                    <div className="text-sm">
                                                        <span className="text-gray-400">TP1:</span>
                                                        <span className="ml-2 text-emerald-400 font-medium">${execution.tp1.toFixed(2)}</span>
                                                    </div>
                                                )}
                                                {execution.tp2 && (
                                                    <div className="text-sm">
                                                        <span className="text-gray-400">TP2:</span>
                                                        <span className="ml-2 text-emerald-400 font-medium">${execution.tp2.toFixed(2)}</span>
                                                    </div>
                                                )}
                                                {execution.tp3 && (
                                                    <div className="text-sm">
                                                        <span className="text-gray-400">TP3:</span>
                                                        <span className="ml-2 text-emerald-400 font-medium">${execution.tp3.toFixed(2)}</span>
                                                    </div>
                                                )}
                                                {execution.tp4 && (
                                                    <div className="text-sm">
                                                        <span className="text-gray-400">TP4:</span>
                                                        <span className="ml-2 text-emerald-400 font-medium">${execution.tp4.toFixed(2)}</span>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Active Positions */}
                        <div className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-6">
                            <h2 className="text-xl font-bold text-white mb-2">Active Positions</h2>
                            <p className="text-sm text-gray-400 mb-6">Current open positions and their performance</p>

                            <div className="space-y-4">
                                {positions.map((position, index) => (
                                    <div key={index} className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-6">
                                        <div className="flex items-center justify-between mb-4">
                                            <div className="flex items-center space-x-3">
                                                <span className={`px-3 py-1 rounded-lg text-xs font-medium ${
                                                    position.side === "LONG"
                                                        ? "bg-emerald-500/20 text-emerald-400"
                                                        : "bg-red-500/20 text-red-400"
                                                }`}>
                                                    {position.side}
                                                </span>
                                                <span className="font-semibold text-white text-lg">{position.symbol}</span>
                                                <span className="px-2 py-1 bg-white/10 rounded-lg text-xs text-gray-300">
                                                    {position.leverage}x
                                                </span>
                                            </div>
                                            <div className={`text-lg font-bold ${position.pnl >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                                                ${position.pnl.toFixed(2)} ({position.pnlPercent >= 0 ? "+" : ""}{position.pnlPercent.toFixed(2)}%)
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                                            <div className="bg-white/5 rounded-xl p-3 border border-white/10">
                                                <p className="text-xs text-gray-400 mb-1">Size</p>
                                                <p className="font-medium text-white">{position.size}</p>
                                            </div>
                                            <div className="bg-white/5 rounded-xl p-3 border border-white/10">
                                                <p className="text-xs text-gray-400 mb-1">Entry Price</p>
                                                <p className="font-medium text-white">${position.entryPrice.toFixed(2)}</p>
                                            </div>
                                            <div className="bg-white/5 rounded-xl p-3 border border-white/10">
                                                <p className="text-xs text-gray-400 mb-1">Mark Price</p>
                                                <p className="font-medium text-white">${position.markPrice.toFixed(2)}</p>
                                            </div>
                                            <div className="bg-white/5 rounded-xl p-3 border border-white/10">
                                                <p className="text-xs text-gray-400 mb-1">Margin</p>
                                                <p className="font-medium text-white">${position.margin.toFixed(2)}</p>
                                            </div>
                                            <div className="bg-white/5 rounded-xl p-3 border border-white/10">
                                                <p className="text-xs text-gray-400 mb-1">Leverage</p>
                                                <p className="font-medium text-white">{position.leverage}x</p>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* Config Tab */}
                {activeTab === "config" && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Default Configuration */}
                        <div className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-6">
                            <div className="flex items-center space-x-3 mb-6">
                                <Settings className="w-6 h-6 text-purple-400" />
                                <div>
                                    <h2 className="text-xl font-bold text-white">Default Configuration</h2>
                                    <p className="text-sm text-gray-400">Configure default trading parameters</p>
                                </div>
                            </div>

                            <div className="space-y-6">
                                <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                                    <label className="block text-base font-medium text-white mb-3">
                                        Default Position Size (USDT)
                                    </label>
                                    <div className="flex items-center space-x-4 mb-2">
                                        <input
                                            type="number"
                                            value={positionSize}
                                            onChange={(e) => setPositionSize(Number(e.target.value))}
                                            className="w-32 px-4 py-2 bg-slate-800 rounded-xl border border-slate-600 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                            min="10"
                                            max="10000"
                                            step="10"
                                        />
                                        <span className="text-sm text-gray-400">Amount to risk per trade</span>
                                    </div>
                                </div>

                                <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                                    <label className="block text-base font-medium text-white mb-4">
                                        Maximum Leverage: {maxLeverage}x
                                    </label>
                                    <input
                                        type="range"
                                        value={maxLeverage}
                                        onChange={(e) => setMaxLeverage(Number(e.target.value))}
                                        min="1"
                                        max="125"
                                        step="1"
                                        className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
                                    />
                                    <div className="flex justify-between text-xs text-gray-400 mt-2">
                                        <span>1x</span>
                                        <span>25x</span>
                                        <span>50x</span>
                                        <span>75x</span>
                                        <span>100x</span>
                                        <span>125x</span>
                                    </div>
                                </div>

                                <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/30 rounded-xl p-6">
                                    <h4 className="font-medium text-white mb-4">Risk Summary</h4>
                                    <div className="space-y-2 text-sm">
                                        <div className="flex justify-between">
                                            <span className="text-gray-400">Position Size:</span>
                                            <span className="font-medium text-white">${positionSize.toLocaleString()}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-400">Max Leverage:</span>
                                            <span className="font-medium text-white">{maxLeverage}x</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-400">Max Position Value:</span>
                                            <span className="font-medium text-white">${(positionSize * maxLeverage).toLocaleString()}</span>
                                        </div>
                                    </div>
                                </div>

                                <button
                                    onClick={savePositionConfig}
                                    className="w-full px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 rounded-xl text-white font-medium transition-all duration-200"
                                >
                                    Save Configuration
                                </button>
                            </div>
                        </div>

                        {/* Manual Trading */}
                        <div className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-6">
                            <div className="flex items-center space-x-3 mb-6">
                                <Play className="w-6 h-6 text-blue-400" />
                                <div>
                                    <h2 className="text-xl font-bold text-white">Manual Trading</h2>
                                    <p className="text-sm text-gray-400">Execute trades with custom parameters</p>
                                </div>
                            </div>

                            <div className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium text-gray-300">Symbol</label>
                                        <select
                                            value={manualTrade.symbol}
                                            onChange={(e) => setManualTrade({ ...manualTrade, symbol: e.target.value })}
                                            className="w-full px-4 py-2 bg-slate-800 rounded-xl border border-slate-600 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                        >
                                            <option value="BTCUSDT">BTCUSDT</option>
                                            <option value="ETHUSDT">ETHUSDT</option>
                                            <option value="ADAUSDT">ADAUSDT</option>
                                            <option value="SOLUSDT">SOLUSDT</option>
                                            <option value="DOTUSDT">DOTUSDT</option>
                                            <option value="LINKUSDT">LINKUSDT</option>
                                        </select>
                                    </div>

                                    <div className="space-y-2">
                                        <label className="text-sm font-medium text-gray-300">Side</label>
                                        <select
                                            value={manualTrade.side}
                                            onChange={(e) => setManualTrade({ ...manualTrade, side: e.target.value as "LONG" | "SHORT" })}
                                            className="w-full px-4 py-2 bg-slate-800 rounded-xl border border-slate-600 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                        >
                                            <option value="LONG">LONG</option>
                                            <option value="SHORT">SHORT</option>
                                        </select>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium text-gray-300">Position Size (USDT)</label>
                                        <input
                                            type="number"
                                            value={manualTrade.positionSize}
                                            onChange={(e) => setManualTrade({ ...manualTrade, positionSize: Number(e.target.value) })}
                                            className="w-full px-4 py-2 bg-slate-800 rounded-xl border border-slate-600 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                            min="10"
                                            max="10000"
                                            step="10"
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        <label className="text-sm font-medium text-gray-300">Leverage</label>
                                        <input
                                            type="number"
                                            value={manualTrade.leverage}
                                            onChange={(e) => setManualTrade({ ...manualTrade, leverage: Number(e.target.value) })}
                                            className="w-full px-4 py-2 bg-slate-800 rounded-xl border border-slate-600 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                            min="1"
                                            max="125"
                                            step="1"
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-gray-300">Stop Loss Price</label>
                                    <input
                                        type="number"
                                        placeholder="Enter stop loss price"
                                        value={manualTrade.stopLoss}
                                        onChange={(e) => setManualTrade({ ...manualTrade, stopLoss: e.target.value })}
                                        className="w-full px-4 py-2 bg-slate-800 rounded-xl border border-slate-600 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                                        step="0.01"
                                    />
                                </div>

                                <div className="space-y-3">
                                    <div className="flex items-center space-x-2">
                                        <Target className="w-4 h-4 text-blue-400" />
                                        <label className="text-sm font-medium text-gray-300">Take Profit Levels</label>
                                    </div>
                                    <div className="grid grid-cols-2 gap-3">
                                        <div className="space-y-1">
                                            <label className="text-xs text-gray-400">TP1</label>
                                            <input
                                                type="number"
                                                placeholder="Take profit 1"
                                                value={manualTrade.takeProfit1}
                                                onChange={(e) => setManualTrade({ ...manualTrade, takeProfit1: e.target.value })}
                                                className="w-full px-3 py-2 bg-slate-800 rounded-xl border border-slate-600 text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                                                step="0.01"
                                            />
                                        </div>
                                        <div className="space-y-1">
                                            <label className="text-xs text-gray-400">TP2</label>
                                            <input
                                                type="number"
                                                placeholder="Take profit 2"
                                                value={manualTrade.takeProfit2}
                                                onChange={(e) => setManualTrade({ ...manualTrade, takeProfit2: e.target.value })}
                                                className="w-full px-3 py-2 bg-slate-800 rounded-xl border border-slate-600 text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                                                step="0.01"
                                            />
                                        </div>
                                        <div className="space-y-1">
                                            <label className="text-xs text-gray-400">TP3</label>
                                            <input
                                                type="number"
                                                placeholder="Take profit 3"
                                                value={manualTrade.takeProfit3}
                                                onChange={(e) => setManualTrade({ ...manualTrade, takeProfit3: e.target.value })}
                                                className="w-full px-3 py-2 bg-slate-800 rounded-xl border border-slate-600 text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                                                step="0.01"
                                            />
                                        </div>
                                        <div className="space-y-1">
                                            <label className="text-xs text-gray-400">TP4</label>
                                            <input
                                                type="number"
                                                placeholder="Take profit 4"
                                                value={manualTrade.takeProfit4}
                                                onChange={(e) => setManualTrade({ ...manualTrade, takeProfit4: e.target.value })}
                                                className="w-full px-3 py-2 bg-slate-800 rounded-xl border border-slate-600 text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                                                step="0.01"
                                            />
                                        </div>
                                    </div>
                                </div>

                                <div className="bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border border-blue-500/30 rounded-xl p-4">
                                    <h4 className="font-medium text-white mb-3 text-sm">Trade Summary</h4>
                                    <div className="grid grid-cols-2 gap-3 text-xs">
                                        <div className="flex justify-between">
                                            <span className="text-gray-400">Position Value:</span>
                                            <span className="font-medium text-white">
                                                ${(manualTrade.positionSize * manualTrade.leverage).toLocaleString()}
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-400">Required Margin:</span>
                                            <span className="font-medium text-white">${manualTrade.positionSize.toLocaleString()}</span>
                                        </div>
                                    </div>
                                </div>

                                <button
                                    onClick={executeManualTrade}
                                    className="w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 rounded-xl text-white font-medium transition-all duration-200 flex items-center justify-center space-x-2"
                                >
                                    <Play className="w-4 h-4" />
                                    <span>Execute Trade</span>
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}