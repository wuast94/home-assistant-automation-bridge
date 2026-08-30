# Wuast Automation Bridge

Home Assistant custom integration for dynamic entities controlled by an external,
self-hosted Python automation runtime. It has no third-party runtime dependencies.

Install it with HACS as a custom integration, restart Home Assistant, then add
**Wuast Automation Bridge** once from Settings → Devices & services.

The authenticated Home Assistant WebSocket API is the only transport. The runtime
calls the integration actions to create, update, and remove entities. Commands from
controllable entities are emitted as `wuast_automation_bridge_command` events and
must be answered with a correlated `command_result` action.

Supported platforms are sensor, binary sensor, switch, light, button, number,
select, and text. Definitions persist in Home Assistant and retain their stable
`unique_id` across restarts.

The generated [API reference](docs/API.md) documents every action, field,
supported platform, command event, and invocation example. A machine-readable
[JSON Schema](docs/entity-definition.schema.json) is published with every release.
