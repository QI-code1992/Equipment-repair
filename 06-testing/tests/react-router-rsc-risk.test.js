const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '../..');
const main = fs.readFileSync(path.join(root, 'codebase/frontend/src/main.tsx'), 'utf8');
const app = fs.readFileSync(path.join(root, 'codebase/frontend/src/App.tsx'), 'utf8');
const manifest = fs.readFileSync(path.join(root, 'codebase/frontend/package.json'), 'utf8');

if (!main.includes('BrowserRouter') || !app.includes('<Routes>')) {
  throw new Error('frontend must remain a BrowserRouter SPA');
}
for (const forbidden of ['react-server', 'react-router-rsc', 'createStaticRouter', 'RouterProvider', 'action:', 'loader:']) {
  if (`${main}\n${app}\n${manifest}`.includes(forbidden)) {
    throw new Error(`GHSA-qwww-vcr4-c8h2 risk boundary violated: ${forbidden}`);
  }
}

console.log('react-router RSC risk boundary checks passed');
