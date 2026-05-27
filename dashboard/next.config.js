/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@policyengine/ui-kit"],
  env: {
    NEXT_PUBLIC_BASE_PATH: "",
  },
};

module.exports = nextConfig;
