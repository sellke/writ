#!/usr/bin/env node

function usage() {
  return [
    "Usage:",
    "  writ date",
    "  writ timestamp [--compact]",
    "  writ --help",
    ""
  ].join("\n");
}

function writeUsage(exitCode) {
  process.stderr.write(usage());
  process.exitCode = exitCode;
}

function pad(value) {
  return String(value).padStart(2, "0");
}

function formatLocalDate(date) {
  return [
    date.getFullYear(),
    pad(date.getMonth() + 1),
    pad(date.getDate())
  ].join("-");
}

function formatUtcTimestamp(date) {
  return date.toISOString().replace(/\.\d{3}Z$/, "Z");
}

function formatCompactUtcTimestamp(date) {
  return [
    date.getUTCFullYear(),
    pad(date.getUTCMonth() + 1),
    pad(date.getUTCDate()),
    "-",
    pad(date.getUTCHours()),
    pad(date.getUTCMinutes()),
    pad(date.getUTCSeconds())
  ].join("");
}

const args = process.argv.slice(2);
const [command, flag] = args;

if (args.length === 1 && command === "--help") {
  writeUsage(0);
} else if (args.length === 1 && command === "date") {
  process.stdout.write(`${formatLocalDate(new Date())}\n`);
} else if (command === "timestamp" && args.length === 1) {
  process.stdout.write(`${formatUtcTimestamp(new Date())}\n`);
} else if (command === "timestamp" && args.length === 2 && flag === "--compact") {
  process.stdout.write(`${formatCompactUtcTimestamp(new Date())}\n`);
} else {
  writeUsage(1);
}
