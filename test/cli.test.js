const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");
const path = require("node:path");
const test = require("node:test");

const cliPath = path.join(__dirname, "..", "bin", "writ.js");

function runCli(args) {
  return spawnSync(process.execPath, [cliPath, ...args], {
    encoding: "utf8"
  });
}

function localDateString(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

test("date prints one local YYYY-MM-DD line", () => {
  const before = localDateString(new Date());
  const result = runCli(["date"]);
  const after = localDateString(new Date());

  assert.equal(result.status, 0);
  assert.equal(result.stderr, "");
  assert.match(result.stdout, /^\d{4}-\d{2}-\d{2}\n$/);
  assert.ok([before, after].includes(result.stdout.trim()));
});

test("timestamp prints one UTC ISO line without milliseconds", () => {
  const result = runCli(["timestamp"]);

  assert.equal(result.status, 0);
  assert.equal(result.stderr, "");
  assert.match(result.stdout, /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\n$/);
});

test("compact timestamp prints filesystem-safe UTC timestamp", () => {
  const result = runCli(["timestamp", "--compact"]);

  assert.equal(result.status, 0);
  assert.equal(result.stderr, "");
  assert.match(result.stdout, /^\d{8}-\d{6}\n$/);
});

test("help prints usage and exits successfully", () => {
  const result = runCli(["--help"]);

  assert.equal(result.status, 0);
  assert.equal(result.stdout, "");
  assert.match(result.stderr, /^Usage:/);
});

test("invalid invocations print usage to stderr and exit non-zero", () => {
  for (const args of [[], ["unknown"], ["timestamp", "--unknown"], ["date", "--compact"]]) {
    const result = runCli(args);

    assert.notEqual(result.status, 0, `expected non-zero exit for ${args.join(" ")}`);
    assert.equal(result.stdout, "");
    assert.match(result.stderr, /^Usage:/);
  }
});
