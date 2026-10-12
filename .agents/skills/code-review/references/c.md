# C lens

For the bootloader, the MicroPython user modules in `f469-disco/usermods/` and other C or build glue.

## Memory safety

- Every buffer access is bounds-checked against the real length, not a length taken from the input.
- Integer overflow and signedness in size and index arithmetic, especially before an allocation or a copy.
- `memcpy`, `strcpy`, `sprintf` and friends: destination size is known and enforced.
- Ownership and lifetime: each allocation freed exactly once on every path including error paths; no use after free; no pointer into a buffer that may be reallocated.
- Uninitialized reads, struct padding leaked into output or storage.

## Secrets and crypto (see backend-security.md)

- Secret buffers are wiped with a call the compiler cannot optimize away.
- Comparison of secrets in constant time.
- No secret in logs, assertions or error strings.

## Embedded rigor

- Interrupt-shared state is volatile or protected; no blocking or allocation in an interrupt handler.
- Stack use is bounded; no large locals or unbounded recursion.
- Flash and persistent writes are atomic or recoverable; wear is considered.
- Watchdog and timeouts on anything that waits on hardware.
- Undefined behavior: shifts by width, signed overflow, strict aliasing, unaligned access on the target.

## MicroPython bindings

- Argument validation and type checks on every function exposed to Python; failures raise, they do not crash.
- Objects handed to Python are kept reachable for the GC for as long as C holds a pointer to them.
- Return values do not alias internal buffers that C will overwrite.

## Testing

- Host-side tests exist for pure logic (see `bootloader/test/`); hardware-only behavior is named as not run.
- Parsers have malformed-input and boundary tests; fuzz targets where practical.
- Warnings are enabled and clean; static analysis findings are addressed or justified.
