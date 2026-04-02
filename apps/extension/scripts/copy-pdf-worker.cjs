const fs = require("fs")
const path = require("path")

const root = path.join(__dirname, "..")
const src = path.join(root, "node_modules", "pdfjs-dist", "build", "pdf.worker.min.mjs")
const destDir = path.join(root, "assets")
const dest = path.join(destDir, "pdf.worker.min.mjs")

fs.mkdirSync(destDir, { recursive: true })
if (fs.existsSync(src)) {
  fs.copyFileSync(src, dest)
} else {
  console.warn("[fairterms] pdf.worker.min.mjs not found; run pnpm install in apps/extension")
}
