import { fileURLToPath } from "node:url";

import path from "node:path";

const __dirname = fileURLToPath(new URL(".", import.meta.url));

console.log("@ alias resolved to:", path.resolve(__dirname, "src"));
