/** @type {import('next').NextConfig} */
const nextConfig = {
  // Allow streaming responses — needed for SSE chat endpoint
  experimental: {
    serverComponentsExternalPackages: ['@azure/cosmos', '@azure/search-documents', 'openai'],
  },
};

export default nextConfig;
