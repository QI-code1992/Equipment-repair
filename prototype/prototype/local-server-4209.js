const http = require("http");
const fs = require("fs");
const path = require("path");

const root = __dirname;
const port = 4209;
const types = { ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "application/javascript; charset=utf-8", ".json": "application/json; charset=utf-8", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".svg": "image/svg+xml", ".ico": "image/x-icon" };

http.createServer((req, res) => {
  const rel = decodeURIComponent(req.url.split("?")[0]) === "/" ? "/pages/intelligent-config.html" : decodeURIComponent(req.url.split("?")[0]);
  const file = path.normalize(path.join(root, rel));
  if (!file.startsWith(root)) return res.writeHead(403).end("Forbidden");
  fs.readFile(file, (error, data) => {
    if (error) return res.writeHead(404).end("Not found");
    res.writeHead(200, {
      "Content-Type": types[path.extname(file).toLowerCase()] || "application/octet-stream",
      "Content-Length": data.length,
      "Cache-Control": "no-store"
    });
    res.end(data);
  });
}).listen(port, "127.0.0.1", () => console.log(`Prototype server: http://127.0.0.1:${port}/pages/intelligent-config.html`));
