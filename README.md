# pyenvgen

Python tool to generate environment variables from schemas.

1. Schemas are defined in a YAML file. They include validation rules based on [marshmallow](https://github.com/marshmallow-code/marshmallow) and custom generation rules.
2. Existing environment variables are read from the storage passed as argument.
3. The tool reads the schema and generates environment variables according to the defined schemas (allowing values to be overridden by existing environment variables or command-line arguments). The resulting environment is validated against the schemas.
4. The generated environment is stored in the specified storage format (e.g., .env file, JSON file, etc.).

## Basic usage

```bash
pyenvgen examples/basic.yaml
```

## Documentation

### Validation Rules

Validation rules are a simple YAML representation of the validation rules supported by the [marshmallow](https://github.com/marshmallow-code/marshmallow) library.

### Generation Rules

- `default`: Use a default value specified in the schema.
- `command`: Generate the value by executing a shell command and using its output.
- `template`: Generate the value by rendering a Jinja2 template, which can include references to other environment variables.
- `openssl`: Use any OpenSSL command to generate the value (uses [pyopenssl](https://github.com/pyca/pyopenssl)). Arguments for the OpenSSL command can be specified in the schema.

### Storage Rules

The generated environment variables can be stored in various formats. For now the supported formats are:
- `stdout`: Print the generated environment variables to standard output.
- `.env`: Write the generated environment variables to a .env file.
- `json`: Write the generated environment variables to a JSON file.
- `toml`: Write the generated environment variables to a TOML file.
- `yaml`: Write the generated environment variables to a YAML file.

### Special Properties

- `internal`: If set to `true`, the generated environment variable will not be included in the output, but it can still be used as a reference in other generation rules (e.g., in templates or commands).
