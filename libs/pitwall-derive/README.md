# pitwall-derive

Procedural macros that power Pitwall's typed telemetry adapters. The primary export is `#[derive(PitwallFrame)]`, which turns a plain Rust struct into a zero-copy adapter capable of validating iRacing schemas and extracting telemetry frames without heap allocations.

Use this crate directly if you want to depend on the macro without pulling the full `pitwall` crate, or disable the `derive` feature in `pitwall` and import the macro manually.

```toml
[dependencies]
pitwall = { version = "0.1", default-features = false }
pitwall-derive = "0.1"
```

Most applications can keep the default `pitwall` feature set, which already re-exports the macro via `pitwall::PitwallFrame`.

## Quick start

```rust
use pitwall::PitwallFrame; // re-exported from the main crate

#[derive(Debug, PitwallFrame)]
pub struct CarData {
    #[field_name = "Speed"]
    pub speed: f32,

    #[field_name = "Gear"]
    pub gear: Option<i32>,

    #[field_name = "FuelLevel"]
    #[missing = "100.0"]
    pub fuel: f32,

    #[calculated = "std::time::Instant::now()"]
    pub timestamp: std::time::Instant,
}
```

During `Pitwall::connect()` or `Pitwall::open()` the generated code validates that the referenced telemetry variables exist. At runtime it performs direct byte slicing—no `HashMap` lookups—so frame construction stays under 1 µs even for very wide structs.

## Attribute reference

| Attribute | Applies to | Description |
|-----------|------------|-------------|
| `field_name = "Var"` | any field | Bind a struct field to an iRacing variable. Required for telemetry-backed fields. |
| `missing = "expr"` | telemetry field | Expression used when the variable is absent. The expression is parsed as Rust code (e.g. `"Default::default()"`). |
| `fail_if_missing` | telemetry field | Treat missing telemetry during schema validation as a hard error instead of falling back. |
| `calculated = "expr"` | field | Evaluate the expression on every frame; use this for timestamps or derived values. |
| `skip` | field | Leave the field untouched. Useful when you populate data manually after receiving the frame. |
| `bitfield(name = ..)` helpers | see below | Work with iRacing bitfield variables. |

### Optional and defaulted fields

- Declare the type as `Option<T>` to get `None` when the variable is missing.
- Keep the type as `T` and add `#[missing = "..."]` to supply a fallback.
- Rely on `T: Default` (no `missing` attribute) for automatic `Default::default()` fallback.

### Bitfield helpers

The derive macro can decode iRacing bitfields into ergonomic booleans or enums:

```rust
#[derive(PitwallFrame)]
pub struct Flags {
    #[field_name = "CarLeftRight"]
    #[bitfield_has(mask = "0b10")]
    pub car_left: bool,

    #[field_name = "EngineWarnings"]
    #[bitfield_map(decoder = "decode_warning")]
    pub warning: Option<EngineWarning>,
}
```

See `pitwall-derive/tests/pass/bitfield_has.rs` and `bitfield_map.rs` for concrete patterns.

## Testing your adapters

Run `cargo test --package pitwall-derive` to execute the `trybuild` suite. The tests compile tiny crates under `tests/pass` and `tests/fail`, ensuring diagnostics stay descriptive. Add new fixtures whenever you extend the macro surface.

## Minimum supported Rust version

MSRV is 1.89 (Rust 2024 edition), matching the main crate. Because the macro emits 2024 edition code, mixing with earlier editions is unsupported.

## License

MIT License. See `LICENSE` in this crate for details.
