# Reverse Engineering Checklists

## Static Triage

- Record SHA-256, SHA-1, MD5, size, path, first-seen source, and whether the artifact is original, dropped, encrypted, decrypted, or unknown.
- Identify container and architecture: PE/ELF/Mach-O/.NET/JAR/APK/script/archive/firmware, 32-bit vs 64-bit, endianness, subsystem, compiler, linker, timestamp, debug paths, and signature state.
- Inspect sections/segments for abnormal permissions, entropy, overlays, packed layouts, resource payloads, TLS callbacks, relocation state, imports, exports, and entry points.
- Extract strings with both ASCII and Unicode passes. Run FLOSS or emulator-assisted decoding when strings are sparse, encoded, or produced only after initialization.
- Run capability tools such as capa and YARA as leads only. Confirm every important rule hit in code before treating it as fact.

## Ghidra Workflow

- Confirm image base, processor language, analysis options, entry points, imports, strings, memory blocks, and undefined code/data gaps.
- Start with anchors: entry, TLS callbacks, exported functions, suspicious imports, high-value strings, crypto constants, indirect dispatch tables, and file/network/registry API xrefs.
- Rename functions with confidence markers when needed: `_candidate`, `_wrapper`, `_dispatcher`, `_confirmed`. Remove markers only after behavior is proven.
- Apply structs to repeated buffers, file headers, config blobs, command tables, object layouts, and protocol packets. Prefer explicit field names over anonymous offsets.
- Leave comments that explain why a conclusion is true: call path, offset, constant, observed value, or matching output. Avoid comments that only restate decompiled code.

## Crypto And Decryption Recovery

- Find entropy-changing boundaries: compression, encoding, encryption, signing, hashing, file copy, and wipe routines.
- Search for constants and APIs tied to AES, ChaCha/Salsa, RSA/ECC, Curve25519, RC4, HC-128, SHA/MD5/BLAKE, BCrypt/CNG, CryptoAPI, OpenSSL, Libsodium, mbedTLS, or custom big-number code.
- Track key material separately from data flow: RNG seed, KDF inputs, machine/user identifiers, embedded public keys, session files, command-line keys, config blobs, memory-resident keys, and wrapped file keys.
- Identify cipher parameters: mode, nonce/IV source, counter layout, block size, padding, authentication tag, chunk size, file marker, and header/trailer serialization.
- Validate with known pairs when available. Compare plaintext/ciphertext offsets, preserved regions, length changes, repeated plaintext blocks, keystream reuse, and whether decrypting one file proves the whole class.

## Ransomware File-Recovery Notes

- Treat encrypted files as evidence. Work on copies, preserve timestamps where useful, and keep source/output directories separate.
- Build a sample matrix by extension, size bucket, directory, encryption marker, and whether a known original exists.
- Look for partial encryption patterns: first N bytes, last N bytes, fixed-size chunks, sparse chunks, every Nth block, file-size thresholds, or format-aware skip regions.
- Inspect companion artifacts: ransom notes, logs, session/state files, dropped tools, configs, scheduled tasks, services, registry keys, and temporary files.
- Recovery scripts should default to dry-run, write a manifest, refuse in-place overwrite unless explicitly requested, and stop on ambiguous headers or unsupported format versions.

## Dynamic Analysis Containment

- Use a disposable VM snapshot with no production credentials, no shared host folders, and controlled networking. Prefer fake services or packet capture over open internet access.
- Capture process tree, command lines, filesystem diff, registry diff, network traffic, mutexes, loaded modules, API traces, and memory dumps around the suspected boundary.
- Break on file I/O, process/service control, crypto APIs, RNG APIs, network connect/send/recv, virtual memory allocation/protection, unpacking transitions, and exception handlers.
- Never run a destructive sample against real victim data. Use minimized synthetic files and copies of encrypted/original pairs only when needed.

## Reporting Template

- Scope: samples, hashes, environment, tools, and exact question being answered.
- Findings: confirmed behaviors with addresses, functions, xrefs, strings, constants, and command outputs.
- Recovery assessment: what is decryptable, what key material is missing, what evidence supports the conclusion, and what validation was performed.
- Artifacts: scripts, config schemas, IOC tables, function maps, decrypted test outputs, and reproduction commands.
- Uncertainty: open hypotheses, failed paths, unsupported file classes, and next evidence needed.
