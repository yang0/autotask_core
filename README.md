# AutoTask Core Plugin

Core plugin for AutoTask that provides essential automation features.

## Node Types

### Environment Key to Value Node
A node that converts environment keys to their corresponding values:

- **Inputs**: 
  - Environment Key 1 (Required)
  - Environment Key 2 (Optional)
  - Environment Key 3 (Optional)
  - All keys are selected from dropdown list

- **Outputs**: 
  - Environment Value 1
  - Environment Value 2
  - Environment Value 3

- **Features**:
  - Dynamic loading of environment options
  - Supports up to 3 key-value conversions
  - Handles missing values gracefully
  - Uses relative path for configuration

## Configuration

The plugin requires an `env.json` file in the `config` directory with the following structure:
```json
[
  {
    "key": "ENV_KEY",
    "value": "env_value",
    "showValue": true
  }
]
```

The configuration file is automatically loaded from the relative path: `../config/env.json`

AutoTask.dev User Id: NazgSJb5PTeueSxSEGbaxT
