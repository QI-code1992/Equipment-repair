const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "../..");
const pages = fs.readdirSync(path.join(root, "03-ui-prototype/prototype/pages")).filter((file) => file.endsWith(".html"));
const app = fs.readFileSync(path.join(root, "03-ui-prototype/prototype/assets/app.js"), "utf8");
const system = fs.readFileSync(path.join(root, "03-ui-prototype/prototype/pages/system-management.html"), "utf8");

const shellPages = pages.filter((file) => !file.endsWith(".artifact.json"));
for (const page of shellPages) {
  const source = fs.readFileSync(path.join(root, "03-ui-prototype/prototype/pages", page), "utf8");
  if (source.includes('class="user-chip"')) {
    if (!app.includes("data-user-menu-trigger") || !app.includes("data-user-action=\"profile\"")) throw new Error("user entry behavior missing");
  }
}
for (const marker of ["user_management.view_all", "data-self-user-view", "tab=users", "当前账号仅可查看", "安全设置 / 修改密码"]) {
  if (!system.includes(marker) && !app.includes(marker)) throw new Error(`missing user management marker: ${marker}`);
}
console.log("user entry and scoped management static checks passed");
