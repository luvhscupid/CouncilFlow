// A stable digest of the dashboard sources, shared by the build and its test.
import { createHash } from "node:crypto";
import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";

function walk(directory, base, out) {
  for (const name of readdirSync(directory, { withFileTypes: true })) {
    const full = path.join(directory, name.name);
    if (name.isDirectory()) walk(full, base, out);
    else out.push(path.relative(base, full).split(path.sep).join("/"));
  }
  return out;
}

export function sourceDigest(root) {
  const files = ["package.json", ...walk(path.join(root, "src"), root, []).sort()];
  const hash = createHash("sha256");
  for (const name of files) {
    // Normalize line endings so Windows checkouts compute the same digest.
    const text = readFileSync(path.join(root, name), "utf8").replace(/\r\n/g, "\n");
    hash.update(`${name}\n${text.length}\n${text}`);
  }
  return hash.digest("hex");
}
