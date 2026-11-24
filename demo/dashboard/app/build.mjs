// Build the CouncilFlow dashboard into one self-contained script for the skill.
// node build.mjs          writes .agents/skills/council-flow/dashboard/app.js
// node build.mjs --check  fails if app.js was not built from the current sources
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { sourceDigest } from "./source-digest.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const output = path.resolve(here, "../../../.agents/skills/council-flow/dashboard/app.js");
const digest = sourceDigest(here);
const banner = `/* CouncilFlow dashboard bundle. Source: demo/dashboard/app (sha256 ${digest}). Built with esbuild; includes React 18.3.1 (MIT). Do not edit by hand. */`;

if (process.argv.includes("--check")) {
  const current = readFileSync(output, "utf8");
  if (!current.startsWith(banner)) {
    console.error("app.js is out of date with demo/dashboard/app/src. Run: npm run build (in demo/dashboard/app)");
    process.exit(1);
  }
  console.log(`app.js matches source ${digest}`);
  process.exit(0);
}

const esbuild = await import("esbuild");
const result = await esbuild.build({
  entryPoints: [path.join(here, "src/main.jsx")],
  bundle: true,
  minify: true,
  format: "iife",
  target: ["es2020"],
  charset: "utf8",
  legalComments: "eof",
  define: { "process.env.NODE_ENV": '"production"' },
  jsx: "automatic",
  write: false,
  logLevel: "warning"
});
let code = result.outputFiles[0].text;
// The template inlines this file inside <script>; keep it from closing the element early.
code = code.replace(/<\/script/gi, "<\\/script");
writeFileSync(output, `${banner}\n${code}`, "utf8");
console.log(`wrote ${path.relative(process.cwd(), output)} (${(Buffer.byteLength(code) / 1024).toFixed(1)} KiB)`);
