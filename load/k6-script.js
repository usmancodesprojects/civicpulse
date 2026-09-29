import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "30s", target: 20 },
    { duration: "2m", target: 80 },
    { duration: "30s", target: 0 },
  ],
  thresholds: { http_req_failed: ["rate<0.01"], http_req_duration: ["p(95)<1000"] },
};

const baseUrl = __ENV.BASE_URL || "http://civicpulse.local";

export default function () {
  const response = http.get(`${baseUrl}/api/complaints?page=1&page_size=20`);
  check(response, { "list succeeds": (result) => result.status === 200 });
  sleep(0.2);
}

