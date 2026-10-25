/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  // FastAPI serves directory indexes for static subpages such as /design-system/.
  trailingSlash: true,
  images: { unoptimized: true },
}

export default nextConfig
