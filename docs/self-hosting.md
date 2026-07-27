# Self-hosting

> **Status: documentation coming soon.** EOS is self-hostable and the reference deployment is
> itself self-hosted, but the server is not published yet, so there is nothing here you can
> follow end to end. This page states what is true today rather than inventing a procedure.

## What is already true

**The CLI is deployment-agnostic by design.** Nothing about a server is compiled into it. The
address travels in the connection file:

```json
{
  "version": 1,
  "server": "https://eos.your-company.internal",
  "project": "payments-gateway",
  "publish_key": "eospk_..."
}
```

That is deliberate, and the reason is worth stating: compiling a URL in would mean one binary
per deployment and a rebuild to move. Carrying it in the connection keeps one-command
onboarding *and* makes self-hosting free. A credential that does not say where to go is not an
invitation.

So `eos connect`, `eos publish` and `eos watch` work against any deployment that implements
the [publish protocol](./protocol.md), with no configuration and no special build.

**Plain HTTP is refused** except against `localhost`, where there is no network to intercept.
A self-hosted deployment needs TLS. This is not configurable, because the alternative is
sending a publish key in the clear.

## Running against a local deployment

If you are developing a server implementation, `http://localhost:<port>` is accepted:

```json
{ "version": 1, "server": "http://localhost:8000", "project": "test", "publish_key": "eospk_..." }
```

## Writing your own server

You do not need the EOS server to use this CLI. The protocol is small — one endpoint, one
header, three JSON fields — and [`docs/protocol.md`](./protocol.md) specifies everything an
implementation needs:

- `POST /api/publish` with an `X-Publish-Key` header
- `GET /api/connect/context` and `GET /api/connect/template`, used only by `connect`

A publisher never needs the connect endpoints: it can take a key from its user and publish.

If you implement one, please open an issue. The protocol specification's acceptance criterion
is that two independent implementations interoperate and produce equivalent results, and it
has not been tested against a second implementation yet.

## What is coming

| | |
|---|---|
| Server distribution | Not published. No container image, no install procedure. |
| Deployment guide | Coming soon — TLS, reverse proxy, database, backups. |
| Conformance suite | Specified and not yet shipped as runnable fixtures. Until it exists, "conforms to the protocol" is a claim nobody can check mechanically. |

Until then: [eos.manaaki.in](https://eos.manaaki.in) is a running deployment, and the protocol
above is enough to build against.
