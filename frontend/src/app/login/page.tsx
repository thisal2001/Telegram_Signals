"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { TrendingUp, Shield, Eye, EyeOff } from "lucide-react";

const Card = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
    <div className={`backdrop-blur-xl bg-white/10 border border-white/20 rounded-3xl shadow-2xl ${className}`}>{children}</div>
);

const CardHeader = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
    <div className={`p-8 pb-4 ${className}`}>{children}</div>
);

const CardTitle = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
    <h1 className={`text-3xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent ${className}`}>
        {children}
    </h1>
);

const CardDescription = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
    <p className={`text-gray-400 mt-2 ${className}`}>{children}</p>
);

const CardContent = ({ children }: { children: React.ReactNode }) => <div className="px-8 pb-8">{children}</div>;

const Button = ({ children, className = "", disabled = false, type = "button", ...props }: any) => (
    <button
        type={type}
        disabled={disabled}
        className={`w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 disabled:from-gray-500 disabled:to-gray-600 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200 transform hover:scale-[1.02] disabled:scale-100 disabled:cursor-not-allowed flex items-center justify-center space-x-2 ${className}`}
        {...props}
    >
        {children}
    </button>
);

const Input = ({ className = "", ...props }: any) => (
    <input
        className={`w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-gray-400 focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition-all duration-200 ${className}`}
        {...props}
    />
);

const Label = ({ children, htmlFor, className = "" }: any) => (
    <label htmlFor={htmlFor} className={`block text-sm font-medium text-gray-300 mb-2 ${className}`}>
        {children}
    </label>
);

const Alert = ({ children, variant = "default", className = "" }: any) => {
    const variantStyles =
        variant === "destructive"
            ? "bg-red-500/20 border-red-500/30 text-red-400"
            : "bg-blue-500/20 border-blue-500/30 text-blue-400";
    return (
        <div className={`flex items-center space-x-2 p-4 border rounded-xl ${variantStyles} ${className}`}>
            {children}
        </div>
    );
};

const AlertDescription = ({ children }: { children: React.ReactNode }) => <span className="text-sm">{children}</span>;

export default function LoginPage() {
    const router = useRouter();
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError("");

        try {
            const res = await fetch("https://tg-message-extractor-2.onrender.com/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password }),
            });

            const data = await res.json();

            if (res.ok) {
                // Save JWT token in localStorage
                localStorage.setItem("token", data.token);
                localStorage.setItem("username", data.username);
                router.push("/dashboard"); // redirect to dashboard
            } else {
                setError(data.message || "Invalid credentials");
            }
        } catch (err) {
            setError("Server error");
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-4 relative overflow-hidden">
            <div className="absolute inset-0 overflow-hidden -z-10">
                <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500/20 rounded-full blur-3xl"></div>
                <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500/20 rounded-full blur-3xl"></div>
            </div>

            <Card className="w-full max-w-md relative">
                <CardHeader className="text-center">
                    <div className="flex items-center justify-center mb-4">
                        <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center">
                            <TrendingUp className="h-8 w-8 text-white" />
                        </div>
                    </div>
                    <CardTitle>Crypto Alert Dashboard</CardTitle>
                    <CardDescription>Sign in to access your Telegram crypto alerts</CardDescription>
                </CardHeader>

                <CardContent>
                    <form onSubmit={handleLogin} className="space-y-6">
                        <div className="space-y-2">
                            <Label htmlFor="username">Username</Label>
                            <Input
                                id="username"
                                type="text"
                                placeholder="Enter your username"
                                value={username}
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setUsername(e.target.value)}
                                required
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="password">Password</Label>
                            <div className="relative">
                                <Input
                                    id="password"
                                    type={showPassword ? "text" : "password"}
                                    placeholder="Enter your password"
                                    value={password}
                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
                                    required
                                    className="pr-12"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                                >
                                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                </button>
                            </div>
                        </div>

                        {error && (
                            <Alert variant="destructive">
                                <Shield className="h-4 w-4 flex-shrink-0" />
                                <AlertDescription>{error}</AlertDescription>
                            </Alert>
                        )}

                        <Button type="submit" disabled={isLoading}>
                            {isLoading ? (
                                <>
                                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                    <span>Signing in...</span>
                                </>
                            ) : (
                                "Sign In"
                            )}
                        </Button>
                    </form>
                </CardContent>
            </Card>
        </div>
    );
}
