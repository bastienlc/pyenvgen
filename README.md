# pyenvgen

> **Warning:** This project was vibe coded and is in early development. Expect breaking changes and incomplete features. Contributions are welcome!

Python tool to generate environment variables from YAML schemas.

1. Define variables in a YAML schema, including types, generation rules, and validation constraints.
2. Existing values are loaded from the chosen storage backend.
3. Values are generated (with existing/overridden values taking precedence), then validated.
4. The final environment is written back to the storage backend.

## Installation

```bash
pip install pyenvgen
```

## Usage

```bash
pyenvgen <schema.yaml> [-s STORAGE] [-b BACKEND] [-o KEY=VALUE ...] [--force]
```

| Flag               | Description                                                                              |
| ------------------ | ---------------------------------------------------------------------------------------- |
| `-s`, `--storage`  | Storage (default: `stdout`), path to a file to store output to.                          |
| `-b`, `--backend`  | Storage backend, when the file extension is ambiguous (e.g. `komodo` vs `toml` backend). |
| `-o`, `--override` | Override a value via `KEY=VALUE` (repeatable)                                            |
| `--force`          | Regenerate all values, ignoring existing stored values                                   |

```bash
# Print to stdout
pyenvgen examples/basic.yaml

# Write to a .env file
pyenvgen examples/basic.yaml -s .env

# Override a value
pyenvgen examples/basic.yaml -o APP_PORT=9000
```

## Schema format

```yaml
variables:
  MY_VAR:
    type: str          # str | int | float | bool (default: str)
    description: "..."
    internal: false    # default: false
    generation:
      rule: default
      value: "hello"
    validation:
      length:
        min: 1
        max: 128
```

### Variable types

`str`, `int`, `float`, `bool`

### Generation rules

All string fields in generation rules are rendered as **Jinja2 templates** against already-generated values before execution.

- **`default`** – use a static value (supports Jinja2, e.g. `"postgres://{{ HOST }}:{{ PORT }}/app"`)
- **`command`** – run a shell command and capture its stdout
- **`openssl`** – generate cryptographic material via the [`cryptography`](https://github.com/pyca/cryptography) package

#### `openssl` commands

| Command   | Description                         | Key args                                                                                    |
| --------- | ----------------------------------- | ------------------------------------------------------------------------------------------- |
| `rsa`     | RSA private key (PEM or DER base64) | `key_size` (default 2048), `encoding` (`pem`\|`der_b64`)                                    |
| `ec`      | EC private key                      | `curve` (`secp256r1`\|`secp384r1`\|`secp521r1`\|`secp256k1`), `encoding` (`pem`\|`der_b64`) |
| `ed25519` | Ed25519 private key                 | `encoding` (`pem`\|`raw_b64`)                                                               |
| `x25519`  | X25519 private key                  | `encoding` (`pem`\|`raw_b64`, default `raw_b64`)                                            |
| `fernet`  | URL-safe base64 Fernet key          | —                                                                                           |
| `random`  | Random bytes                        | `length` (default 32), `encoding` (`hex`\|`base64`\|`base64url`)                            |

### Validation rules

Backed by [marshmallow](https://github.com/marshmallow-code/marshmallow).

| Rule     | Applies to     | Fields                                         |
| -------- | -------------- | ---------------------------------------------- |
| `length` | `str`          | `min`, `max`                                   |
| `range`  | `int`, `float` | `min`, `max`, `min_inclusive`, `max_inclusive` |
| `one_of` | any            | `choices: [...]`                               |
| `regexp` | any            | `pattern`                                      |

### Storage backends

| Value    | Description                                                          |
| -------- | -------------------------------------------------------------------- |
| `stdout` | Print to standard output                                             |
| `.env`   | Read/write a `.env` file                                             |
| `json`   | Read/write a JSON file                                               |
| `toml`   | Read/write a TOML file                                               |
| `yaml`   | Read/write a YAML file                                               |
| `komodo` | Read/write a [Komodo](https://github.com/moghtech/komodo)-style TOML |

### Special properties

- **`internal: true`** – the variable is generated and available to Jinja2 templates but excluded from the output.
