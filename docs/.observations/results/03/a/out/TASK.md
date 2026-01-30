# Agent Output from Session A, Prompt 1 (Task Prompt)

```markdown
Got it. I’ll inventory and map **all authentication/authorization-related code** by (1) locating likely entrypoints via targeted repo-wide searches (without using `code_search`), (2) reading the key modules/middleware/guards, then (3) producing a concise architecture map of **who issues/validates tokens vs who consumes claims/roles**, plus security-relevant patterns and any risks I notice. I’ll start by scanning for authn/authz keywords and common framework hooks.

You’re right—the repo-wide greps timed out because the codebase is large (and includes `node_modules`/`venv`). I’ll follow the error guidance by re-running **more targeted searches** scoped to likely source roots (`backend/`, `client/`, `frontend/`, `deploy/`, `docs/`) and filtering to relevant file types, avoiding vendor dirs. Then I’ll read the key auth/authz entrypoints and produce the requested map.
I’ve now narrowed the search to real source directories (excluding `node_modules`/`venv`) and found the core authn/authz modules in `backend/server/internal/{auth,oidc,middleware,iam}` plus client OAuth flow code and deploy-time `dex` + [oauth2-proxy](cci:9://file:///home/jgodau/work/dsg/geoanalytics/platform/containers/oauth2-proxy:0:0-0:0) manifests. Next I’ll open the key files to map responsibilities and security-relevant behaviors (token validation, claims extraction, role checks, etc.).

# Authentication + Authorization Map (GeoAnalytics Platform)

## Files related to **authentication** (OAuth2/OIDC, tokens, sessions, login flows)

### Backend (Go server)
- **[backend/server/internal/auth/authenticate.go](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/auth/authenticate.go:0:0-0:0)**
  - **Purpose:** Single entrypoint to authenticate a request.
  - **Flow:**
    1. Try `Authorization: Bearer <jwt>` (direct API access).
    2. If that fails, fall back to **cookie-based auth** by calling [auth.request(GET, EndpointAuth, ...)](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/frontend/ui/features/http/services.ts:66:2-69:3) + `auth.FetchUser()` (this is the “session via oauth2-proxy” path).
  - **OIDC integration:** constructs issuer as `getBaseURL() + "/dex"` and fetches JWKS to validate bearer tokens.

- **[backend/server/internal/middleware/auth.go](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/middleware/auth.go:0:0-0:0)**
  - **Purpose:** Gin middleware wrapping [auth.Authenticate](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/auth/authenticate.go:14:0-66:1).
  - **Behavior:** On success, stores username in a **Gorilla session** (`session.Store.Get`, `sesh.Values[session.KeyUser] = ...`, `sesh.Save`), and also stores session + username in gin context.
  - **Also contains:** [AsRole()](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/middleware/auth.go:56:0-103:1) header-based impersonation (details under authz).

- **[backend/server/internal/middleware/jwtclaims.go](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/middleware/jwtclaims.go:0:0-0:0)**
  - **Purpose:** Core JWT extraction + validation + claim hydration used by CRD-backed routers.
  - **Token sources:**
    - `Authorization: Bearer ...`
    - Cookie `cookieName` (passed in from router wiring; currently `ga-session` in [main.go](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/cmd/main.go:0:0-0:0))
  - **Validation:** RSA signature validation using JWKS from `https://<host>/dex/keys`.
  - **Post-validation:** looks up user via CRD controller (`UserController.Get` or `GetByEmail`) and **injects platform/project roles** into [auth.GeoAnalyticsClaims](cci:2://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/auth/claims.go:11:0-25:1) ([auth.InjectClaimsValues](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/auth/claims.go:49:0-58:1)).

- **[backend/server/internal/auth/token_controller.go](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/auth/token_controller.go:0:0-0:0)**
  - **Purpose:** Exposes API endpoints to retrieve tokens for UI / external clients.
  - **Routes registered under [/auth](cci:9://file:///home/jgodau/work/dsg/geoanalytics/platform/client/cli/auth:0:0-0:0):**
    - `GET/POST /auth/token/authorize`
    - `GET /auth/token/callback`
    - `GET /auth/token/status`
    - `GET /auth/token/current`
    - `GET /auth/token/list`
    - `DELETE /auth/token/revoke/:id`
    - `POST /auth/token/create`
  - **Important note:** This controller mixes multiple concepts:
    - Extract bearer tokens from headers
    - Attempts to use oauth2-proxy cookies (`ga-proxy`/`ga-session`) and do a token-exchange against Dex if the cookie “looks like a JWT”
    - Has a “scoped token” generator that is **not an OAuth token** (random string).

- **[backend/server/internal/auth/token.go](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/auth/token.go:0:0-0:0)**
  - **Purpose:** Implements [TokenManager](cci:2://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/auth/token.go:115:0-122:1) used by [TokenController](cci:2://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/auth/token_controller.go:18:0-26:1).
  - **Implements:** OAuth2 authorization code + PKCE flow via OIDC discovery at `.../dex/.well-known/openid-configuration`.
  - **Also implements:** refresh token request to token endpoint.
  - **Also implements:** [CreateScopedToken()](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/auth/token.go:514:0-539:1) generating random tokens (not JWT).

- **`backend/server/internal/oidc/*`**
  - **Key files:**
    - [oidc/client.go](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/oidc/client.go:0:0-0:0): OIDC discovery, JWKS fetch/cache, userinfo, token exchange, refresh, validate, claim extraction.
    - [oidc/jwks.go](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/oidc/jwks.go:0:0-0:0): JWKS RSA parsing helpers.
    - [oidc/claims.go](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/oidc/claims.go:0:0-0:0): helpers extracting email/username.

- **[backend/server/internal/env/dex.go](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/env/dex.go:0:0-0:0)** / **[backend/server/internal/env/oauth2.go](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/env/oauth2.go:0:0-0:0)** (found via grep)
  - **Purpose:** server-side configuration plumbing for Dex/OAuth2 client IDs, issuer URLs, connectors.

- **[backend/server/cmd/main.go](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/cmd/main.go:0:0-0:0)**
  - **Purpose:** wires middleware and routers.
  - **Auth-relevant wiring:**
    - `mw := middleware.NewMiddleware(config); rg.Use(mw...)`
    - CRD-backed routers use [JWTClaimsMiddleware(jwtSecret, jwtCookie, ...)](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/middleware/jwtclaims.go:45:0-146:1)
    - **Currently:** `jwtSecret := "your_jwt_secret"` and `jwtCookie := "ga-session"` are hard-coded TODOs.

### Frontend (Next/React UI)
- **[frontend/ui/features/http/services.ts](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/frontend/ui/features/http/services.ts:0:0-0:0)**
  - Uses `axios` with `withCredentials: true` to send cookies.
  - On `401`, redirects browser to:
    - `/login/start?redirect=<current-path>`
  - Explicitly documents assumption: oauth2-proxy + nginx external auth inject `Authorization` header; UI itself does not manage bearer tokens.

- **[frontend/ui/features/token/services.ts](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/frontend/ui/features/token/services.ts:0:0-0:0)**
  - Calls API:
    - `API.AUTH.TOKEN_CURRENT` → `GET /auth/token/current`
    - `API.AUTH.TOKEN_AUTHORIZE` → `GET /auth/token/authorize`
  - Returns `{ accessToken, expiresIn }` from server response.

- **[frontend/ui/components/profile/TokenDisplay.tsx](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/frontend/ui/components/profile/TokenDisplay.tsx:0:0-0:0)**
  - Displays / generates “personal access token” for external tools (QGIS).
  - Uses `useAccessToken()` + `useGenerateToken()` hooks (not read here, but clearly consume TokenController endpoints).

### CLI Client (Go)
- **[client/internal/auth/oauth2.go](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/client/internal/auth/oauth2.go:0:0-0:0)**
  - Implements OAuth2 authorization code + PKCE by opening a browser + local callback server.
  - Uses `config.Get().AuthURL` and `config.Get().TokenURL`.
  - Supports refresh token flow.
  - Contains experimental “token exchange” helper using `golang.org/x/oauth2` options.

- **[client/internal/auth/auth.go](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/client/internal/auth/auth.go:0:0-0:0)**
  - Wraps credential cache; [Login()](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/client/internal/auth/auth.go:54:0-63:1) does PKCE flow; [Refresh()](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/client/internal/auth/auth.go:65:0-83:1) uses refresh token.

### Deploy / Infra (Dex + oauth2-proxy)
- **[deploy/platform/values/auth.values.yaml](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/deploy/platform/values/auth.values.yaml:0:0-0:0)**
  - Defines oauth2-proxy cookie name `ga-proxy`, clientId, clientSecret, cookie refresh/expiry, dex token expiry settings, etc.
  - **Security note:** this file includes what look like base64-encoded secrets (still sensitive even if base64).

- **[deploy/platform/templates/ingress/oauth2proxy.yaml](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/deploy/platform/templates/ingress/oauth2proxy.yaml:0:0-0:0)**
  - nginx external auth setup:
    - `nginx.ingress.kubernetes.io/auth-response-headers: Authorization`
  - Routes `/login(.*)` to oauth2-proxy service.

- **`deploy/platform/templates/dex/*`**, **`deploy/platform/templates/oauth2/*`**
  - Dex deployment/configmaps and oauth2-proxy deployment/configmaps/secrets (found via grep list; not individually opened here except ingress/values).

---

## Files related to **authorization** (RBAC, permissions, role checks)

### Backend (Go server)
- **[backend/server/internal/auth/claims.go](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/auth/claims.go:0:0-0:0)**
  - Defines [GeoAnalyticsClaims](cci:2://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/auth/claims.go:11:0-25:1):
    - identity (`Username`, `Email`, `AccountID`, `CurrentProject`)
    - authorization (`PlatformRoles`, `ProjectRoles`, `HighestRoleLevel`)
  - [InjectClaimsValues()](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/auth/claims.go:49:0-58:1) maps CRD `UserSpec.Policies` into platform/project roles and sets highest role.

- **[backend/server/internal/auth/roles.go](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/auth/roles.go:0:0-0:0)**
  - [HasPlatformRole(claims, role)](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/auth/roles.go:6:0-14:1)
  - [HasProjectRole(claims, role)](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/auth/roles.go:16:0-24:1)

- **[backend/server/internal/middleware/jwtclaims.go](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/middleware/jwtclaims.go:0:0-0:0)**
  - Provides authorization guards:
    - [RequirePlatformRole(requiredRoles...)](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/middleware/jwtclaims.go:284:0-309:1)
    - [RequireProjectRole(requiredRoles...)](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/middleware/jwtclaims.go:311:0-338:1)
  - Implements a **platform-admin bypass** for all checks.
  - Also sets `CurrentProject` via [UpdateCurrentProjectInJWT()](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/middleware/jwtclaims.go:340:0-353:1).

- **[backend/server/internal/middleware/auth.go](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/middleware/auth.go:0:0-0:0)**
  - [AsRole()](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/middleware/auth.go:56:0-103:1) allows **platform admin** to impersonate:
    - `X-GeoAnalytics-AsRole: platformProjectAdmin|platformUser`
  - It mutates `claims.PlatformRoles` in-context.

- **Routers using authorization**
  - **[backend/server/internal/routers/iam.go](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/routers/iam.go:0:0-0:0)**
    - Applies [JWTClaimsMiddleware](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/middleware/jwtclaims.go:45:0-146:1) to all endpoints.
    - Uses [RequirePlatformRole(platformAdmin, platformProjectAdmin)](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/middleware/jwtclaims.go:284:0-309:1) for IAM listing endpoints.
  - **[backend/server/internal/routers/users.go](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/routers/users.go:0:0-0:0)**
    - Applies [JWTClaimsMiddleware](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/middleware/jwtclaims.go:45:0-146:1) to all endpoints.
    - Some endpoints do manual role checks from claims (`isPlatformAdmin`, etc.).
    - Some endpoints use [middleware.RequirePlatformRole(...)](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/middleware/jwtclaims.go:284:0-309:1).

### “IAM” meaning in this repo
There are two “IAM” concepts:
- **Platform RBAC** (your app-level roles/policies)
  - Enforced via [GeoAnalyticsClaims](cci:2://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/auth/claims.go:11:0-25:1) + middleware role checks + CRD policy lists.
- **Azure RBAC** (cloud resource permissions)
  - Implemented in [backend/server/internal/iam/controller.go](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/iam/controller.go:0:0-0:0) and `backend/clientset/azure/*` (e.g. [azureroleassignment.go](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/clientset/azure/azureroleassignment.go:0:0-0:0)), managing Azure role assignments, managed identities, etc.

---

# Component responsibility map (who handles auth vs who consumes it)

## AuthN “issuers / validators”
- **Issuer / identity provider:** **Dex** (`/dex`) deployed via Helm templates.
- **Login/session front door:** **oauth2-proxy** under `/login/*`, with nginx external auth annotations.
- **JWT validation (server-side):**
  - [middleware.JWTClaimsMiddleware()](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/middleware/jwtclaims.go:45:0-146:1) validates JWT signature against Dex JWKS (`/dex/keys`).
  - [auth.authenticateWithBearerToken()](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/auth/authenticate.go:68:0-144:1) validates bearer token via OIDC client + JWKS.

## AuthN “consumers”
- **Backend API routers**
  - CRD-backed routes: consume claims from [JWTClaimsMiddleware](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/middleware/jwtclaims.go:45:0-146:1).
  - Other routes (legacy?) consume [middleware.auth()](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/middleware/auth.go:16:0-54:1) which calls [auth.Authenticate()](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/auth/authenticate.go:14:0-66:1) and sets Gorilla session.

- **Frontend UI**
  - Consumes session via cookie (`withCredentials: true`) and relies on oauth2-proxy/nginx to handle auth headers.
  - Uses token endpoints to fetch a bearer token for external use.

- **CLI**
  - Does direct OIDC OAuth2+PKCE against Dex token endpoint and stores bearer tokens locally.

## AuthZ (role/policy checks)
- **Enforcement points:**
  - [middleware.RequirePlatformRole](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/middleware/jwtclaims.go:284:0-309:1), [middleware.RequireProjectRole](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/middleware/jwtclaims.go:311:0-338:1)
  - ad-hoc checks in routers (e.g., [routers/users.go](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/routers/users.go:0:0-0:0))
  - [AsRole()](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/middleware/auth.go:56:0-103:1) for admin impersonation

- **Source of truth for roles:**
  - Ultimately derived from **User CRD** policies (`user.Spec.Policies`) via [auth.InjectClaimsValues()](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/auth/claims.go:49:0-58:1).
  - Claims may also contain some identity info from JWT, but roles are *hydrated/overwritten* from CRD lookup.

---

# Security-relevant patterns & findings

## Good / expected patterns
- **OIDC discovery + JWKS validation** exists ([oidc.Client.Discover](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/oidc/client.go:55:0-99:1), [JWKS](cci:2://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/oidc/jwks.go:22:0-33:1) caching).
- **PKCE** used in:
  - CLI ([client/internal/auth/oauth2.go](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/client/internal/auth/oauth2.go:0:0-0:0))
  - Server [TokenManager](cci:2://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/auth/token.go:115:0-122:1) ([backend/server/internal/auth/token.go](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/auth/token.go:0:0-0:0))
- **401 vs 403 behavior** is explicitly handled in frontend interceptor (401 redirects to login; 403 does not).

## Security concerns / things to review closely
- **Hard-coded JWT secret in [main.go](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/cmd/main.go:0:0-0:0)**
  - `jwtSecret := "your_jwt_secret"` is a serious footgun if this is used in any meaningful way. Even if currently unused (since RSA JWKS is used), it suggests config drift or incomplete migration.

- **Token validation does not appear to enforce issuer/audience/expiry explicitly in some paths**
  - [auth.authenticateWithBearerToken()](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/auth/authenticate.go:68:0-144:1) uses `jwt.Parse` with keyfunc and checks RSA signature. Unless options are configured elsewhere, it may not strictly validate `iss/aud/exp/nbf`.
  - [JWTClaimsMiddleware](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/middleware/jwtclaims.go:45:0-146:1) uses `jwt.ParseWithClaims` similarly; again signature is validated, but strict registered-claim validation depends on how `jwt/v5` is configured (not obvious here).
  - Recommendation: confirm whether the library auto-validates `exp/nbf` and whether you ever validate `iss`/`aud`.

- **[fetchRSAPublicKeyForDex()](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/middleware/jwtclaims.go:170:0-207:1) uses `http.Get` with a host derived from request**
  - It builds `https://<host>/dex/keys` using `c.Request.Host`.
  - This creates a potential **SSRF / host-header injection** risk if the service is reachable with arbitrary `Host` headers (depends on ingress/proxy/trusted proxy config).
  - Safer pattern: use configured issuer base URL, not request host.

- **Duplicate token validation implementations**
  - There are at least two JWT/JWKS validation paths:
    - [auth.authenticateWithBearerToken()](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/auth/authenticate.go:68:0-144:1) + [oidc.Client.JWKS()](cci:2://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/oidc/jwks.go:22:0-33:1)
    - [middleware.JWTClaimsMiddleware()](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/middleware/jwtclaims.go:45:0-146:1) + custom [fetchRSAPublicKeyForDex()](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/middleware/jwtclaims.go:170:0-207:1)
  - Increases drift risk (one path might enforce different rules).

- **[TokenController](cci:2://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/auth/token_controller.go:18:0-26:1) / [TokenManager](cci:2://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/auth/token.go:115:0-122:1) mix “real OAuth tokens” with “random scoped tokens”**
  - [CreateScopedToken()](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/auth/token.go:514:0-539:1) generates a random string and stores it as if it were a token.
  - This is not a JWT and not verifiable by other services unless they consult this in-memory map.
  - Also: the in-memory map means tokens die on restart and aren’t shared across replicas.
  - If this is intended as “PAT” functionality, it likely needs a persistent store and a clear validation middleware.

- **Secrets in repo**
  - [deploy/platform/values/auth.values.yaml](cci:7://file:///home/jgodau/work/dsg/geoanalytics/platform/deploy/platform/values/auth.values.yaml:0:0-0:0) contains base64 secrets; base64 is not protection. This should be treated as exposed credentials.

- **[AsRole()](cci:1://file:///home/jgodau/work/dsg/geoanalytics/platform/backend/server/internal/middleware/auth.go:56:0-103:1) impersonation lacks explicit denial path**
  - If not admin, the middleware ends without calling `Abort` or `Next()`. That can result in confusing request hangs or bypass depending on Gin behavior and route chain.
  - Also, impersonation is controlled by a request header; confirm audit logging / traceability requirements.

---

# Status

- **Completed:** repo-wide auth/authz discovery (scoped searches), file inventory, responsibility map, and security-pattern review (no `code_search` used).
```