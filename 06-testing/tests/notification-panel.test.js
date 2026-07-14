const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "../..");
const app = fs.readFileSync(path.join(root, "03-ui-prototype/prototype/assets/app.js"), "utf8");
const css = fs.readFileSync(path.join(root, "03-ui-prototype/prototype/assets/app.css"), "utf8");
const pages = fs.readdirSync(path.join(root, "03-ui-prototype/prototype/pages")).filter((file) => file.endsWith(".html"));
if (!app.includes("initNotificationCenter") || !app.includes("notification-bell-icon")) throw new Error("notification center or SVG bell missing");
const workbench = fs.readFileSync(path.join(root, "03-ui-prototype/prototype/pages/workbench.html"), "utf8");
if (!workbench.includes('class="icon-btn"') || !workbench.includes("铃")) throw new Error("workbench notification trigger shell missing");
for (const marker of ["data-notification-filter", "data-notification-read-all", "data-notification-more", "暂无未读消息", "消息通知"]) {
  if (!app.includes(marker)) throw new Error(`missing notification behavior: ${marker}`);
}
for (const marker of ["notification-bell-icon", "notification-badge", "notification-panel", ".topbar-actions > .icon-btn{position:relative}"]) {
  if (!css.includes(marker)) throw new Error(`missing notification style: ${marker}`);
}
console.log("notification panel static checks passed");
