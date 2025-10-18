import http from 'k6/http';
import { sleep } from 'k6';

export const options = { stages: [ { duration: '30s', target: 20 }, { duration: '1m', target: 100 } ] };

export default function () {
  const res = http.get('http://localhost:8000/search?q=beach%20at%20sunset&k=10');
  sleep(1);
}
