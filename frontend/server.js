const express = require('express');
const path = require('path');

const app = express();

const distPath = path.join(
  __dirname,
  'dist',
  'tinymoviecatalog-frontend',
  'browser'
);

// Servir les fichiers Angular
app.use(express.static(distPath));

// Rediriger les routes Angular vers index.html
app.get('/{*splat}', (req, res) => {
  res.sendFile(path.join(distPath, 'index.html'));
});

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`Application disponible sur http://localhost:${PORT}`);
});