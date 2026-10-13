# Data Module ITM-WEB-CORS-001 — CORS and API Platform ownership

**Issue:** 001  
**Information code:** System description / fault isolation  
**Example organisation:** IndiaOne Bank (fictional; 100 crore customers).

## 1. Definition

**Cross-Origin Resource Sharing (CORS)** is a browser-enforced mechanism that uses HTTP response headers to decide whether scripts running on one web origin may read responses from another. An origin is the tuple **scheme + host + port**.

CORS does **not** determine whether a customer is authenticated, authorised to access a loan account, or permitted to perform a transaction. Browsers enforce CORS; many non-browser API clients do not. Protect the API with independent authentication and authorisation.

## 2. Example

- Frontend: `https://portal.indiaone.example`
- Backend API: `https://api.indiaone.example`
- Request: browser JavaScript calls `GET /loans/statement`.
- If a preflight is required, the browser sends an `OPTIONS` request before the actual request.
- API gateway or backend responds with applicable `Access-Control-Allow-Origin`, methods and headers (and credential settings as needed).
- Browser decides whether frontend JavaScript can read the response.
- Backend separately checks customer identity and ownership of the loan record.

For **100 crore customers**, CORS typically applies to approved *website origins*, not to individual customer accounts.

## 3. Ownership

| Boundary | Function |
|---|---|
| Frontend | Detects browser console error; confirms origin, method and request headers |
| Backend | Defines or serves CORS headers if application-owned; secures customer data |
| API Gateway/API Platform | Defines, applies and monitors CORS if gateway-owned |
| AppSec | Reviews allowlist policy and security exceptions |
| Infra/Network | Assists only when network, ingress or reverse proxy settings are relevant |
| CISO | Governs security programme and significant escalations; not necessarily each routine CORS change |

## 4. Failure mode

Old allowed origin: `https://old.indiaone.example`  
New frontend: `https://new.indiaone.example`

If the new origin is not approved, the browser may block JavaScript from reading the response, even if a direct authorised API client succeeds. Determine whether the *gateway, ingress, reverse proxy or backend* is the configuration owner before assigning a fix.

**Security constraint:** Do not casually replace a narrow origin allowlist with wildcard `*` for sensitive APIs. Credentialed cross-origin requests require specific compatible headers and controls.

## 5. Diagnostic procedure

1. Reproduce in a browser. Record the exact failed request and origin.
2. Check whether the failing request is a preflight `OPTIONS` or the actual operation.
3. Inspect the relevant response headers, redirect chain and status code.
4. Identify which infrastructure or service writes CORS headers.
5. Determine the permitted origin under the approved policy; request risk review if outside it.
6. Deploy, regression-test approved origins and verify unrelated origins remain blocked.

**Do not confuse:** API Platform = organisational capability/team; API Gateway = component; Backend = service containing business logic.
