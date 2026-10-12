# Backend and security lens

For code that handles keys, seeds, signing, parsing of untrusted input, persistent state or the bootloader. Each item is a question to answer from the code; mark it SAFE, UNSAFE or NOT APPLICABLE with the evidence.

The three [Core Invariants](../../../../AGENTS.md#core-invariants) come first and apply to every diff, not only to the paths that select this lens. This file says how to check them.

## Invariant 1: entropy is random

- Entropy the device generates comes from the hardware RNG path, never from a general-purpose PRNG, a timer, a counter or any guessable value.
- A failed or missing entropy source raises an error. There is no weaker fallback.
- Other entropy (dice, user input) is mixed in so it can only add, never replace or reduce the device's own.
- Nonces are never reused and never derived from low-entropy input.
- Generated values are not logged or cached where a later step could reuse them.

## Invariant 2: keys stay safe

- Seed, private keys and passphrase leave their protected storage only through a flow the user explicitly started (for example showing the recovery phrase for a backup), and only as far as that flow needs.
- They are not logged, printed, put in exception messages, sent over a host link, written to storage unencrypted, or left in debug output. Check the debug build paths too.
- Wipe buffers where the runtime allows it and note where it cannot. Do not keep secrets longer than needed.
- A crash or power loss mid-write cannot lose or corrupt the seed, a wallet or settings.
- Comparison of secrets and MACs: note if the runtime cannot be constant-time and whether that matters on a device with no remote timing observer.

## Invariant 3: what you see is what you sign

- The text shown for confirmation and the data that is signed come from the same parsed object. Nothing is re-parsed between display and signing, and a change to the data after confirmation invalidates the confirmation.
- Shown values are factually correct: amounts and units, fee, each destination address, network, script type and derivation path.
- Hidden details are hidden honestly. When the user's settings show fewer details, what remains is still true (a summary says "3 more outputs", it does not leave them out silently).
- Change outputs are identified correctly and cannot be misattributed or redirected.
- PSBT fields that alter what is signed (sighash type, unknown or proprietary fields, inputs not owned by this wallet) cannot slip past the display.
- Malformed or hostile input fails cleanly; it cannot reach a state where the user is shown something different from what is signed.
- The same holds for message signing and any other signing flow.

## Other cryptographic checks

- Key derivation follows the BIPs it claims (BIP32, 39, 44, 48, 49, 84, 86); hardened paths are used where required; passphrases are handled as specified.
- Signature handling: malleability, low-S, Schnorr (BIP340/341/342) correctness where used.
- Do not invent or hand-roll primitives. Use the audited library already in the tree.

## Bitcoin protocol compliance

- BIP and format references claimed by the change (PSBT BIP174/370, descriptors, address types) are implemented as specified, including edge cases and test vectors.
- Script and policy limits are enforced where the code builds or validates scripts.
- Fee, amount and change handling: overflow, underflow, dust, change detection, units (sat versus BTC).
- Time locks (CSV, CLTV) and RBF signaling are preserved, not dropped.

## Untrusted input and transport (host links, QR, SD card, serial)

Specter has no peer-to-peer network stack today. Treat every external channel as an untrusted peer. This section also applies if a networked protocol is ever added.

- Parsers check bounds and sizes before allocating or indexing; no unbounded reads; clear failure on malformed input.
- Response size is bounded relative to request size.
- State machines accept only valid transitions; unexpected message order does not corrupt state.
- Fuzz or property-test targets exist for each parser (see the testing section of the language lens).

## Systems rigor

- Resource use is bounded: allocations in loops, queues, buffers, open files and handles are closed on every path.
- Error handling: no silent `except: pass`, errors carry context and the state needed to diagnose them, no failure path leaves half-written state.
- Persistent writes are atomic or recoverable; checksums or versioning detect corruption; schema or format changes have a migration path.
- Timeouts on anything that waits on the outside world.
- Logging: structured where the project has it, no secrets, enough to debug on a device without a debugger.
- Defaults are fail-closed. Configuration that can weaken security is explicit and visible.

## Production readiness (for release-bound changes)

Backward compatibility with existing stored data, rollback or recovery path, upgrade path tested, new dependencies reviewed for supply-chain risk and license, documentation of the threat model touched.

## Escalate to the user

Changes to cryptographic code, to anything that moves or signs funds, to the bootloader, or to the storage format. Ask before proceeding; do not decide alone.
