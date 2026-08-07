import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("../..", import.meta.url)));
const css = readFileSync(resolve(root, "codebase/frontend/src/styles.css"), "utf8");
const genericGridRule = ".data-card { grid-column: span 2; }";
const workbenchOverride = ".workbench-metric-grid > .workbench-metric, .workbench-primary-grid > .workbench-queue-card { grid-column: auto; }";

assert.notEqual(css.indexOf(genericGridRule), -1, "generic two-column card rule must remain explicit");
assert.notEqual(css.indexOf(workbenchOverride), -1, "workbench cards must override the generic two-column card rule");
assert.ok(
  css.indexOf(workbenchOverride) > css.indexOf(genericGridRule),
  "workbench override must follow the generic card rule so the prototype grid wins the cascade",
);

console.log("workbench grid cascade: PASS");
