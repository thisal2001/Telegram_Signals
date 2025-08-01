"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    const isAuthenticated = localStorage.getItem("auth") === "true";

    if (isAuthenticated) {
      router.replace("/dashboard"); // Redirect to dashboard
    } else {
      router.replace("/login"); // Redirect to login
    }
  }, [router]);

  return (
    <div className="flex items-center justify-center h-screen">
      <p className="text-gray-600 text-lg">Redirecting...</p>
    </div>
  );
}
