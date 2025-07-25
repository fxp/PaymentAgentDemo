import express from 'express';

const app = express();
app.use(express.json());

const DETAILS = { '1': { id: '1', name: 'ACME Corp', description: 'A company' } };

app.get('/company/basic', (req, res) => {
  const keyword = req.query.keyword || '';
  const data = Object.values(DETAILS).filter(c => c.name.includes(keyword)).map(({id,name})=>({id,name}));
  res.json({ data });
});

app.get('/company/detail', (req, res) => {
  const id = req.query.id;
  if (!req.headers['x-payment-token']) {
    return res.status(402).json({ price: 10 });
  }
  const detail = DETAILS[id] || null;
  res.json(detail);
});

app.post('/pay', (req, res) => {
  const { tokenId, amount } = req.body;
  // TODO: validate tokenId
  res.json({ success: true });
});

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`Marketplace API listening on ${port}`));
