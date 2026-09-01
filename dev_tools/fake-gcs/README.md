# fake-gcs (local only)

A local [fake-gcs-server](https://github.com/fsouza/fake-gcs-server) so the ML pipeline can
run end to end on a laptop without real Google Cloud Storage credentials. **Never used by
dev or production** - those set real credentials and leave `STORAGE_EMULATOR_HOST` unset.

## Start / stop

```sh
docker compose -f dev_tools/fake-gcs/compose.yaml up -d
docker compose -f dev_tools/fake-gcs/compose.yaml down
```

Then set this in each `projects/<svc>/.env` you want to run against it (and **restart** the
consumer - `.env` is read once at startup):

```
STORAGE_EMULATOR_HOST=http://localhost:4443
```

`4443` is fake-gcs-server's own default port; `-p 4443:4443` just publishes it. The
`google-cloud-storage` library reads `STORAGE_EMULATOR_HOST` itself and routes every
request there instead of `storage.googleapis.com`.

## Buckets

fake-gcs-server turns each top-level directory under `data/` into a bucket on startup, so
the four pipeline buckets already exist:

| bucket | written by | read by |
| --- | --- | --- |
| `similar_protein` | `blast` / `mmseqs2` (query stage) | `evotune` |
| `unirep` | `evotune` | `fittop`, `mutation` |
| `ridgecv` | `fittop` | `mutation` |
| `mutation` | `mutation` (final artifact) | frontend download |

Add another bucket: `mkdir dev_tools/fake-gcs/data/<name>` and restart the container.

## Inspect / reset

```sh
curl -s localhost:4443/storage/v1/b                       # list buckets
curl -s localhost:4443/storage/v1/b/similar_protein/o     # list objects in a bucket
```

Written objects are held **in memory** - `docker compose -f dev_tools/fake-gcs/compose.yaml
down` (or `up` again) clears them. Nothing is written back into `data/`; the `.gitignore`
entry for `data/*/*` is only a safety net in case a future image version changes that.
