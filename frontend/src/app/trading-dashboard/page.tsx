"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Slider } from "@/components/ui/slider"
import { RefreshCw, TrendingUp, TrendingDown, DollarSign, Shield, Zap, Settings } from "lucide-react"

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
    const [positionSize, setPositionSize] = useState(1000)
    const [maxLeverage, setMaxLeverage] = useState([20])

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
        console.log("Saving position config:", { positionSize, maxLeverage: maxLeverage[0] })
    }

    return (
        <div className="container mx-auto p-6 space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Trading Dashboard</h1>
                    <p className="text-muted-foreground">Monitor your Binance futures trading activity</p>
                </div>
                <Button onClick={refreshData} disabled={isLoading} variant="outline">
                    <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
                    Refresh
                </Button>
            </div>

            {account && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Total Balance</CardTitle>
                            <DollarSign className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">${account.totalBalance.toFixed(2)}</div>
                            <p className="text-xs text-muted-foreground">USDT</p>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Available Balance</CardTitle>
                            <Zap className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">${account.availableBalance.toFixed(2)}</div>
                            <p className="text-xs text-muted-foreground">Ready to trade</p>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Total Margin</CardTitle>
                            <Shield className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">${account.totalMargin.toFixed(2)}</div>
                            <p className="text-xs text-muted-foreground">In positions</p>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Total PnL</CardTitle>
                            {account.totalPnl >= 0 ? (
                                <TrendingUp className="h-4 w-4 text-green-600" />
                            ) : (
                                <TrendingDown className="h-4 w-4 text-red-600" />
                            )}
                        </CardHeader>
                        <CardContent>
                            <div className={`text-2xl font-bold ${account.totalPnl >= 0 ? "text-green-600" : "text-red-600"}`}>
                                ${account.totalPnl.toFixed(2)}
                            </div>
                            <p className={`text-xs ${account.totalPnlPercent >= 0 ? "text-green-600" : "text-red-600"}`}>
                                {account.totalPnlPercent >= 0 ? "+" : ""}
                                {account.totalPnlPercent.toFixed(2)}%
                            </p>
                        </CardContent>
                    </Card>
                </div>
            )}

            <Tabs defaultValue="dashboard" className="space-y-6">
                <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
                    <TabsTrigger value="config">Position Config</TabsTrigger>
                </TabsList>

                <TabsContent value="dashboard" className="space-y-6">
                    <Card>
                        <CardHeader>
                            <CardTitle>Recent Trade Executions</CardTitle>
                            <CardDescription>Latest automated trade executions from signals</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {executions.map((execution) => (
                                    <div key={execution.id} className="border rounded-lg p-4 space-y-3">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center space-x-3">
                                                <Badge variant={execution.setupType === "LONG" ? "default" : "secondary"}>
                                                    {execution.setupType}
                                                </Badge>
                                                <span className="font-semibold">{execution.symbol}</span>
                                                <Badge variant="outline">{execution.leverage}x</Badge>
                                            </div>
                                            <div className="text-sm text-muted-foreground">
                                                {new Date(execution.timestamp).toLocaleString()}
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                            <div>
                                                <p className="text-muted-foreground">Quantity</p>
                                                <p className="font-medium">{execution.quantity}</p>
                                            </div>
                                            <div>
                                                <p className="text-muted-foreground">Avg Price</p>
                                                <p className="font-medium">${execution.avgPrice.toFixed(2)}</p>
                                            </div>
                                            <div>
                                                <p className="text-muted-foreground">Stop Loss</p>
                                                <p className="font-medium text-red-600">${execution.stopLoss.toFixed(2)}</p>
                                            </div>
                                            <div>
                                                <p className="text-muted-foreground">Status</p>
                                                <Badge variant={execution.status === "FILLED" ? "default" : "secondary"}>
                                                    {execution.status}
                                                </Badge>
                                            </div>
                                        </div>

                                        <div>
                                            <p className="text-sm text-muted-foreground mb-2">Take Profit Targets</p>
                                            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                                                {execution.tp1 && (
                                                    <div className="text-sm">
                                                        <span className="text-muted-foreground">TP1:</span>
                                                        <span className="ml-1 text-green-600">${execution.tp1.toFixed(2)}</span>
                                                    </div>
                                                )}
                                                {execution.tp2 && (
                                                    <div className="text-sm">
                                                        <span className="text-muted-foreground">TP2:</span>
                                                        <span className="ml-1 text-green-600">${execution.tp2.toFixed(2)}</span>
                                                    </div>
                                                )}
                                                {execution.tp3 && (
                                                    <div className="text-sm">
                                                        <span className="text-muted-foreground">TP3:</span>
                                                        <span className="ml-1 text-green-600">${execution.tp3.toFixed(2)}</span>
                                                    </div>
                                                )}
                                                {execution.tp4 && (
                                                    <div className="text-sm">
                                                        <span className="text-muted-foreground">TP4:</span>
                                                        <span className="ml-1 text-green-600">${execution.tp4.toFixed(2)}</span>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle>Active Positions</CardTitle>
                            <CardDescription>Current open positions and their performance</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {positions.map((position, index) => (
                                    <div key={index} className="border rounded-lg p-4">
                                        <div className="flex items-center justify-between mb-3">
                                            <div className="flex items-center space-x-3">
                                                <Badge variant={position.side === "LONG" ? "default" : "secondary"}>{position.side}</Badge>
                                                <span className="font-semibold">{position.symbol}</span>
                                                <Badge variant="outline">{position.leverage}x</Badge>
                                            </div>
                                            <div className={`text-lg font-bold ${position.pnl >= 0 ? "text-green-600" : "text-red-600"}`}>
                                                ${position.pnl.toFixed(2)} ({position.pnlPercent >= 0 ? "+" : ""}
                                                {position.pnlPercent.toFixed(2)}%)
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                                            <div>
                                                <p className="text-muted-foreground">Size</p>
                                                <p className="font-medium">{position.size}</p>
                                            </div>
                                            <div>
                                                <p className="text-muted-foreground">Entry Price</p>
                                                <p className="font-medium">${position.entryPrice.toFixed(2)}</p>
                                            </div>
                                            <div>
                                                <p className="text-muted-foreground">Mark Price</p>
                                                <p className="font-medium">${position.markPrice.toFixed(2)}</p>
                                            </div>
                                            <div>
                                                <p className="text-muted-foreground">Margin</p>
                                                <p className="font-medium">${position.margin.toFixed(2)}</p>
                                            </div>
                                            <div>
                                                <p className="text-muted-foreground">Leverage</p>
                                                <p className="font-medium">{position.leverage}x</p>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="config" className="space-y-6">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Settings className="h-5 w-5" />
                                Position Configuration
                            </CardTitle>
                            <CardDescription>
                                Configure your trading parameters for automated position sizing and risk management
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div className="space-y-3">
                                <Label htmlFor="position-size" className="text-base font-medium">
                                    Default Position Size (USDT)
                                </Label>
                                <div className="flex items-center space-x-4">
                                    <Input
                                        id="position-size"
                                        type="number"
                                        value={positionSize}
                                        onChange={(e) => setPositionSize(Number(e.target.value))}
                                        className="w-32"
                                        min="10"
                                        max="10000"
                                        step="10"
                                    />
                                    <span className="text-sm text-muted-foreground">Amount to risk per trade</span>
                                </div>
                                <p className="text-sm text-muted-foreground">
                                    This is the base amount that will be used for each trade before leverage is applied.
                                </p>
                            </div>

                            <div className="space-y-4">
                                <Label className="text-base font-medium">Maximum Leverage: {maxLeverage[0]}x</Label>
                                <div className="px-2">
                                    <Slider
                                        value={maxLeverage}
                                        onValueChange={setMaxLeverage}
                                        max={125}
                                        min={1}
                                        step={1}
                                        className="w-full"
                                    />
                                    <div className="flex justify-between text-xs text-muted-foreground mt-1">
                                        <span>1x</span>
                                        <span>25x</span>
                                        <span>50x</span>
                                        <span>75x</span>
                                        <span>100x</span>
                                        <span>125x</span>
                                    </div>
                                </div>
                                <p className="text-sm text-muted-foreground">
                                    Maximum leverage allowed for any trade. The system will not exceed this limit regardless of signal
                                    recommendations.
                                </p>
                            </div>

                            <div className="border rounded-lg p-4 bg-muted/50">
                                <h4 className="font-medium mb-2">Risk Summary</h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                    <div>
                                        <span className="text-muted-foreground">Position Size:</span>
                                        <span className="ml-2 font-medium">${positionSize.toLocaleString()}</span>
                                    </div>
                                    <div>
                                        <span className="text-muted-foreground">Max Leverage:</span>
                                        <span className="ml-2 font-medium">{maxLeverage[0]}x</span>
                                    </div>
                                    <div>
                                        <span className="text-muted-foreground">Max Position Value:</span>
                                        <span className="ml-2 font-medium">${(positionSize * maxLeverage[0]).toLocaleString()}</span>
                                    </div>
                                    <div>
                                        <span className="text-muted-foreground">Required Margin:</span>
                                        <span className="ml-2 font-medium">${positionSize.toLocaleString()}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="flex justify-end">
                                <Button onClick={savePositionConfig} className="w-full md:w-auto">
                                    Save Configuration
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    )
}
