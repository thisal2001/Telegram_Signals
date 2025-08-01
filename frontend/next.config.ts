/** @type {import('next').NextConfig} */
const nextConfig = {
    eslint: {
        ignoreDuringBuilds: true, // ✅ Skip ESLint errors in Vercel build
    },
};

export default nextConfig;
