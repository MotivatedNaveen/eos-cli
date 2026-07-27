<!-- Mirrored from the Engineering OS repository, which holds the normative copy.
     Cross-references to internal decision records have been flattened to plain
     text; nothing else is changed. Edit it upstream, not here. -->

# The EOS Publish Protocol — v1

> **Status:** Draft · **Layer:** Universal · **Owner:** Founding Engineer
> **Completes:** ADR-0016's promise of
> "one spec, two forms" — the file form is `.engos`; this is the transport form.
> **Scoped by:** ADR-0020

This document defines **everything an independent implementation needs to publish engineering
memory to an EOS deployment**, and nothing else.

The governing test for every statement in this specification:

> **Must an independent implementation know this to interoperate correctly?**

If a different client could reasonably choose differently without breaking interoperability,
it does not belong here — it is client behaviour, and lives in a client ADR.

## Acceptance criterion

A minimal publish client can be implemented from this document alone, without importing or
reading any EOS implementation code. Two implementations written only from this document must
interoperate with the same deployment and produce **equivalent results** for the same
Engineering Layer.

"Equivalent results" means the deployment ends in the same state — not that the two clients
produce byte-identical HTTP bodies. Byte-identity is not required, because the content digest
is client-local state (see §10).

## Conformance language

**MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT** and **MAY** are used as in RFC 2119.

---

## 1. Transport

```
POST {server}/api/publish
Content-Type: application/json
X-Publish-Key: {key}
```

- Requests MUST be HTTPS, except against `localhost` where a deployment MAY serve plain HTTP.
  A client MUST NOT send a publish key over plain HTTP to any other host.
- The request body MUST be UTF-8 encoded JSON.
- A client MUST send `Content-Length`. A deployment MAY refuse a request without one (411).
- This endpoint is **not** cookie-authenticated and is exempt from CSRF. A client MUST NOT be
  required to obtain any cookie, token or session to publish.

## 2. Authentication

The `X-Publish-Key` header carries a **publish key**: an opaque bearer credential that
authorizes exactly one action — replacing one project's protocol — in exactly one organization.

- A key is scoped to a single project. It grants no read access, no administrative capability,
  and nothing outside its project.
- A deployment MUST answer identically for a key that is unknown, revoked, or expired. A client
  therefore learns only that this key does not work, never why.
- A client MUST NOT log the key, place it in a URL, or pass it as a command-line argument.

## 3. The payload

```json
{
  "project": "busos",
  "engos_version": "0.1",
  "files": {
    ".engos/manifest.yaml": "schema_version: 1\nengos_version: '0.1'\n…",
    "docs/decisions/0001-x.md": "# ADR-0001 …"
  }
}
```

| Field | Type | Required | Meaning |
|---|---|---|---|
| `project` | string | yes | The project identifier this payload belongs to (§4) |
| `engos_version` | string | yes | The `.engos` content schema version this payload conforms to (§8) |
| `files` | object | yes, non-empty | Relative path → complete file content |

- A deployment MUST ignore fields it does not recognise (§8.3).
- `files` MUST contain at least one entry, and MUST contain `.engos/manifest.yaml` (§7).

## 4. Project identity

**`payload.project` MUST equal the project identifier the presented key authorizes.**

A deployment MUST reject a mismatch with **403**, naming the project the key authorizes.

This is the protocol's identity rule, and it has one practical consequence worth stating
plainly: the `project:` value in `.engos/manifest.yaml` and the identifier the deployment knows
the project by **are the same string**. A repository whose manifest says `engineering-os` cannot
publish with a key issued for `eos`.

A deployment MUST NOT infer identity from anything else — not the payload's contents, not the
request's origin, not a repository. The key determines the organization; `project` determines
which project within it.

## 5. Path selection — what constitutes the Engineering Layer

A client MUST include every file under these roots, relative to the repository root:

```
.engos/        structured engineering state
docs/          the taxonomy (constitution, decisions, standards, knowledge, journal)
discovery/     observations
```

A client MUST exclude:

- files outside those roots, including `CLAUDE.md`, source code, and build output
- `.gitkeep` placeholder files
- any file whose bytes are not valid UTF-8 (§6.1)

A client SHOULD report excluded files rather than dropping them silently.

A deployment MUST reject any path outside those roots with **422**. Path selection is therefore
protocol, not deployment policy: a client cannot construct a valid payload without knowing it.

> **Not yet specified.** Whether `.gitignore` applies within these roots, and whether a
> repository may relocate them (a manifest-declared footprint), are open questions inherited
> from ADR-0016. Until settled, the roots above are fixed and literal.

## 6. Normalization

This section is the one most likely to make two honest implementations disagree. Every rule
here exists because omitting it produces silent divergence rather than an error.

### 6.1 Content

- File content MUST be valid **UTF-8**, represented as a JSON string.
- A client MUST strip a UTF-8 BOM if present.
- **Line endings MUST be normalized to `LF` (`\n`) on the wire.** A client reading `CRLF` from
  disk MUST convert before sending.

  Without this rule, the same commit published from Windows and from Linux CI stores different
  content, and the deployment shows churn that is not engineering change. This is not
  hypothetical: repositories with `core.autocrlf` produce `CRLF` working trees from `LF` blobs.
- A client MUST NOT otherwise alter content: no trailing-whitespace stripping, no reformatting,
  no trailing-newline insertion or removal.
- Content MAY be empty.

### 6.2 Paths

- Paths MUST use `/` as the separator, MUST be relative, and MUST NOT contain `.`, `..`, a
  leading `/`, a drive letter, or a colon.
- Paths MUST be Unicode **NFC**-normalized. macOS decomposes filenames (NFD); without this,
  the same file publishes under two different keys depending on the client's platform.
- Paths are **case-sensitive**. Two paths differing only in case are two files.
  A client SHOULD NOT emit paths differing only in case: a deployment storing them on a
  case-insensitive filesystem would collapse them, and the loss would be silent.
- A deployment MUST reject any violation of the first rule with **422**, and MUST verify after
  resolution that the target remains inside the project's store.

### 6.3 What is deliberately not normalized

Ordering. `files` is a JSON object; its member order carries no meaning and a deployment MUST
NOT depend on it. A client MAY emit any order.

## 7. Replace semantics

**A publish is a complete snapshot, and replaces the project's stored protocol wholesale.**

- Files present in `files` are written.
- **Files absent from `files` are deleted.** Deletion is implicit; there is no delete operation
  and no partial update.
- A publish is **idempotent**: publishing identical content twice leaves the same state.
- A publish is therefore **safe to retry** after a timeout or a network failure, with no risk
  of duplication or partial application.

A deployment MUST NOT apply a payload partially. If a payload is rejected, the previously
stored protocol MUST remain intact and unchanged.

## 8. Versioning and compatibility

Three version numbers exist and are frequently confused. Only the first two appear in this
protocol.

| Version | Where | Versions what |
|---|---|---|
| `engos_version` | payload + manifest | the `.engos` **content schema** |
| this specification | out of band | the **wire contract** |
| `schema_version` | inside each `.engos/*.yaml` | that individual file's shape |

`STANDARD_STAMP` — the version of the artifacts the EOS Factory installs (`CLAUDE.md`, git
hooks) — is **not** part of this protocol. Those files never cross this wire.

### 8.1 What a client sends

A client MUST send the `engos_version` declared in `.engos/manifest.yaml`. A client MUST NOT
invent, default, or upgrade it.

### 8.2 What a deployment accepts

- A deployment MUST accept payloads whose major version matches its own current major.
- A deployment **SHOULD** accept the immediately preceding major, so that a client is never
  forced to upgrade in lockstep with a server.
- A deployment MUST reject a **newer** major with **422**: it cannot interpret content whose
  schema postdates it.
- A deployment MUST reject a missing or unparseable `engos_version` with **422**.

> **Known delta.** At the time of writing only major version `0` exists, and the reference
> implementation accepts exactly that. ADR-0016 promises "the engine supports the last N
> versions"; this section is that promise made precise, with N ≥ 2 once a second major exists.
> The reference implementation must be updated to expose and honour a range when that happens.

### 8.3 Forward compatibility

A deployment MUST ignore payload fields it does not recognise. This is what allows the payload
to gain optional fields within a major version without breaking existing clients.

Correspondingly, a client MUST tolerate unrecognised fields in a response.

## 9. Concurrency and ordering

**Last write wins. There is no ordering guarantee and no concurrency control.**

Two publishers publishing the same project concurrently will produce one of the two states,
and the protocol does not define which. There is no compare-and-swap, no version precondition,
and no rejection of a stale publish.

Clients that need a single coherent published state SHOULD ensure only one publisher publishes
a given project — for example by publishing from one branch, or from CI rather than from
developer machines. **That is client behaviour, and this specification does not require it.**

> A future version MAY add an optional precondition (an `If-Match`-style digest) to make
> concurrent publishing detectable. It is deliberately absent from v1: adding it later is
> additive, and specifying it now would define semantics nobody has needed yet.

## 10. Content digest

A client MAY compute a digest of the payload to skip redundant publishes.

The digest is **client-local state**. It is not sent, not stored by the deployment, and not
part of this protocol. Two implementations MAY compute it differently. This is why §Acceptance
requires equivalent results rather than byte-identical payloads.

## 11. Limits

- A deployment MUST document its maximum request body size and MUST reject a larger request
  with **413**, based on the declared `Content-Length`, before reading the body.
- The reference implementation's limit is **32 MiB**.
- A client SHOULD surface a 413 as an actionable message; it is not retryable without change.

## 12. Responses

### 12.1 Success — `200`

```json
{
  "ok": true,
  "project": "busos",
  "files_written": 110,
  "engos_version": "0.1",
  "message": "Protocol for 'busos' published and projected."
}
```

`message` is human-facing and MUST NOT be parsed.

### 12.2 Failures

| Status | Meaning | Retryable |
|---|---|---|
| **401** | Key missing, unknown, revoked, or expired — indistinguishable by design | No, without a new key |
| **403** | The key is valid, but `project` is not the project it authorizes (§4) | No |
| **411** | No `Content-Length` | No, without change |
| **413** | Body exceeds the deployment's limit (§11) | No, without change |
| **422** | Not a valid protocol payload: missing or incompatible `engos_version`, missing manifest, or an unsafe path | No, without change |
| **429** | Rate limited. `Retry-After` gives seconds | Yes, after the delay |
| **5xx** | Deployment fault | Yes, with backoff |

Every failure body is JSON with a `detail` string. A client MUST NOT depend on its wording.

**A 4xx is never retried unchanged.** A client that retries a 422 in a loop is a client that
will be rate-limited.

## 13. What this protocol deliberately does not contain

Stated so implementers do not go looking, and so future additions are deliberate:

- **Repository identity.** A deployment does not learn which repository published. "One key,
  one repository" is therefore not enforced. Adding a fingerprint is a future protocol change,
  not a client convention (ADR-0019 §6).
- **Branch.** A deployment cannot tell which branch a publish came from.
- **Authorship, timestamps, commit identity.** Nothing about git crosses this wire.
- **Engineering conformance.** A payload that is structurally valid is accepted even if its
  engineering content is incomplete or inconsistent
  (ADR-0020).
- **Onboarding.** `/api/connect/*` is a separate, separately-versioned protocol. A publisher
  never needs it: it can take a key from its user and publish.

## 14. Conformance

An implementation conforms if it satisfies every MUST in this document.

A conformance suite — fixtures of requests and expected outcomes — is required alongside this
specification, and the reference implementation must be validated against it. Without that, the
specification drifts from the code and the code wins, which is exactly how the transport form
came to be undocumented in the first place.

### Known deltas in the reference implementation

Recorded so the specification is normative rather than descriptive:

1. **The accepted version range (§8.2)** is not exposed, and exactly one major is accepted.
   This is the delta that matters: it is the clause ADR-0016 already promised and the code
   already contradicts.
2. **The conformance suite (§14)** does not exist as shippable fixtures. The normalization
   clauses (§5, §6) are covered by `tests/test_protocol_conformance.py`, which is a start but
   is written against the reference implementation rather than published for others to run.

---

*Draft. Adopted by an ADR once the conformance suite exists and the deltas above are either
closed or accepted with reasons.*
