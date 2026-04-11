/**
 * SovereignFace Backend Server
 * ─────────────────────────────────────────────────────────────────────
 * Stores biometric scan records (face photos + credentials) persistently.
 * Accessible from any device on the same network via http://<your-ip>:3000
 *
 * Endpoints:
 *   GET    /api/scans          – list all scan records
 *   GET    /api/scans/:id      – get single record by id
 *   POST   /api/scans          – save a new scan record
 *   DELETE /api/scans/:id      – delete a specific record
 *   DELETE /api/scans          – clear all records
 *
 * Run: node server.js
 * ─────────────────────────────────────────────────────────────────────
 */

const express = require('express');
const cors    = require('cors');
const fs      = require('fs');
const path    = require('path');
const os      = require('os');

const app  = express();
const PORT = 3000;
const DATA_FILE = path.join(__dirname, 'scans_data.json');

// ── Middleware ────────────────────────────────────────────────────────
app.use(cors({ origin: '*' }));            // allow all origins (cross-host)
app.use(express.json({ limit: '20mb' })); // allow large base64 photos
app.use(express.static(__dirname));        // serve HTML files directly

// ── Data helpers ──────────────────────────────────────────────────────
function readData() {
  try {
    return JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
  } catch {
    return [];
  }
}

function writeData(records) {
  fs.writeFileSync(DATA_FILE, JSON.stringify(records, null, 2), 'utf8');
}

// Initialise file if missing
if (!fs.existsSync(DATA_FILE)) writeData([]);

// ── Routes ────────────────────────────────────────────────────────────

// GET all records (most recent first)
app.get('/api/scans', (req, res) => {
  res.json(readData());
});

// GET single record
app.get('/api/scans/:id', (req, res) => {
  const record = readData().find(r => String(r.id) === req.params.id);
  if (!record) return res.status(404).json({ error: 'Not found' });
  res.json(record);
});

// POST – save new scan record
app.post('/api/scans', (req, res) => {
  const records = readData();
  const record  = {
    ...req.body,
    id:      req.body.id || Date.now(),
    savedAt: new Date().toISOString(),
  };
  records.unshift(record);
  writeData(records);
  console.log(`[+] Scan saved  id=${record.id}  user=${record.username}`);
  res.json({ success: true, id: record.id });
});

// DELETE single
app.delete('/api/scans/:id', (req, res) => {
  const records = readData().filter(r => String(r.id) !== req.params.id);
  writeData(records);
  res.json({ success: true });
});

// DELETE all
app.delete('/api/scans', (req, res) => {
  writeData([]);
  res.json({ success: true });
});

// ── Start ─────────────────────────────────────────────────────────────
app.listen(PORT, '0.0.0.0', () => {
  // Show local + network IPs so user knows what URL to share
  const networkIPs = Object.values(os.networkInterfaces())
    .flat()
    .filter(i => i.family === 'IPv4' && !i.internal)
    .map(i => i.address);

  console.log('\n╔══════════════════════════════════════════════════╗');
  console.log('║  SovereignFace Backend  ●  Running               ║');
  console.log('╠══════════════════════════════════════════════════╣');
  console.log(`║  Local   →  http://localhost:${PORT}                ║`);
  networkIPs.forEach(ip =>
    console.log(`║  Network →  http://${ip}:${PORT}  `.padEnd(52) + '║')
  );
  console.log('╠══════════════════════════════════════════════════╣');
  console.log('║  Open the network URL from any device on your    ║');
  console.log('║  Wi-Fi / LAN to access the app cross-host.       ║');
  console.log('╚══════════════════════════════════════════════════╝\n');
});
