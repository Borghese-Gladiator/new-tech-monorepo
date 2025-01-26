import express from 'express';
import cors from 'cors';
import { FRONTEND_URL } from 'shared-utils';
// import {utils} from "@myorg/utils";

//==================
//  CONSTANTS
//==================
const host = process.env.HOST ?? 'localhost';
const port = process.env.PORT ? Number(process.env.PORT) : 3000;

const app = express();

//==================
//  Middleware
//==================
app.use(express.json());
app.use(cors({
  origin: FRONTEND_URL || 'http://localhost:4200',
  methods: ['GET', 'POST'],
  allowedHeaders: ['Content-Type']
}));

//==================
//  Endpoints
//==================
app.get('/', (req, res) => {
  res.send({ message: 'Hello API' });
});
app.get('/api/todos', (req, res) => {
  res.json([
    { id: 1, title: 'Buy groceries', completed: false },
    { id: 2, title: 'Walk the dog', completed: true },
  ]);
});

app.listen(port, host, () => {
  console.log(`[ ready ] http://${host}:${port}`);
});
