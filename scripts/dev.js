/**
 * ShiVi - Cross-Platform Zero-Dependency Dev Runner
 * Spawns both Backend (FastAPI Python) and Frontend (Next.js) concurrently
 * with color-coded log prefixing, zero shell interpolation issues, and unified graceful shutdown.
 */

const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

const ROOT_DIR = path.resolve(__dirname, "..");
const BACKEND_DIR = path.join(ROOT_DIR, "backend");
const FRONTEND_DIR = path.join(ROOT_DIR, "frontend");

const cyan = (text) => `\x1b[36m${text}\x1b[0m`;
const magenta = (text) => `\x1b[35m${text}\x1b[0m`;
const red = (text) => `\x1b[31m${text}\x1b[0m`;
const green = (text) => `\x1b[32m${text}\x1b[0m`;

console.log(green("================================================================================"));
console.log(green("  🚀 SHIVI - SMART HYBRID INTELLIGENT VIRTUAL INTEGRATION (DEV RUNNER)"));
console.log(green("================================================================================"));
console.log(`  • Backend Service:  ${cyan("http://localhost:8000")} (Swagger: /docs)`);
console.log(`  • Frontend Web COP: ${magenta("http://localhost:3000")}`);
console.log(green("================================================================================"));

// Detect Python executable (prefer venv if present)
const isWindows = process.platform === "win32";
const venvPythonPath = path.join(ROOT_DIR, "..", "ShiVi,", ".venv", "Scripts", isWindows ? "python.exe" : "python");
const pythonCmd = fs.existsSync(venvPythonPath) ? venvPythonPath : "python";

// 1. Spawn Backend Process (direct binary, no shell to prevent path delimiter issues)
const backendProcess = spawn(pythonCmd, ["server.py"], {
  cwd: BACKEND_DIR,
  shell: false,
  stdio: ["inherit", "pipe", "pipe"],
  env: { ...process.env, PORT: "8000", HOST: "0.0.0.0" },
});

backendProcess.stdout.on("data", (data) => {
  const lines = data.toString().trim().split("\n");
  lines.forEach((line) => console.log(`${cyan("[BACKEND]")} ${line}`));
});

backendProcess.stderr.on("data", (data) => {
  const lines = data.toString().trim().split("\n");
  lines.forEach((line) => console.error(`${cyan("[BACKEND]")} ${red(line)}`));
});

// 2. Spawn Frontend Process (direct Node execution of Next.js runner)
const nextRunner = path.join(FRONTEND_DIR, "scripts", "run-next.js");
const frontendProcess = spawn(process.execPath, [nextRunner, "dev"], {
  cwd: FRONTEND_DIR,
  shell: false,
  stdio: ["inherit", "pipe", "pipe"],
  env: { ...process.env, PORT: "3000" },
});

frontendProcess.stdout.on("data", (data) => {
  const lines = data.toString().trim().split("\n");
  lines.forEach((line) => console.log(`${magenta("[FRONTEND]")} ${line}`));
});

frontendProcess.stderr.on("data", (data) => {
  const lines = data.toString().trim().split("\n");
  lines.forEach((line) => console.error(`${magenta("[FRONTEND]")} ${red(line)}`));
});

// Graceful Shutdown
function shutdown() {
  console.log("\n" + red("[RUNNER] Shutting down ShiVi microservices..."));
  backendProcess.kill("SIGTERM");
  frontendProcess.kill("SIGTERM");
  process.exit(0);
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
