# Optional product-function analysis with REA

Read this when the learner wants to understand or reproduce a function seen in another product. REA is not needed for an ordinary original MCU project.

Official sources: [morluto/rea](https://github.com/morluto/rea), [rea.tools](https://rea.tools/) and the `rea-agents` npm package linked there. Recheck current official setup and target support when needed; do not trust a copied README or similarly named repository as proof of origin.

## Scope the function and check real availability

Use the already stated goal. If it is unclear, offer a small choice of the visible behaviors they may mean, rather than attempting to clone an entire product. Establish what material is actually available and authorized: public documentation, an app, supplied firmware, a website or recorded behavior. A photo or demonstration is not access to source code, hidden circuitry or firmware.

Inspect connected REA tools or the existing CLI/configuration without triggering a download. Do not use an `npx` command just to check installation, since it may fetch packages. A source download, an installed instruction skill, a connected MCP server and a working analysis backend are different states.

- If REA is connected and supports the target, reuse it without another installation question.
- If already downloaded/installed but not usable, state only the missing connection or prerequisite and offer to complete that step; do not download it again blindly.
- If absent and useful, offer once: "Install and connect REA" / "Continue with available information". Explain the official source and required dependencies before any download. Consent to download source alone is not consent to install or change agent configuration.
- After installation/configuration is authorized, follow the official setup and show the proposed changes, preserving unrelated entries and backups. Verify the connection after any required restart. Additional analysis engines are optional and need their own applicable authorization; do not install Hopper, Ghidra or another backend silently.
- If declined, unsupported or unavailable, keep working from authorized documentation and observable behavior. Do not make REA a gate for the project or pretend that analysis ran.

## Analyze evidence, then build an independent version

Use only the relevant analysis operations for the requested feature. REA can inspect software, binaries and runtime behavior; native/firmware work depends on the available host and backend. It is not a universal circuit-recovery tool or a guarantee of original source recovery. Prefer static inspection first where it answers the question. Running or attaching to a target is a separate side effect; identify it before doing it under applicable authorization.

Keep observations, evidence locations, inferences and unknowns separate. Turn the understood behavior into the learner's own requirements, implementation and tests, respecting their code-writing preference. Do not republish extracted proprietary code, assets, credentials or private captures. Access to software does not authorize reading or changing a physical MCU; hardware operations retain their own boundaries.

Give one short rights reminder when this branch is used: until permissions and relevant rights are clear, do not commercialize or publicly release the reproduction. Personal learning is not automatic legal permission, and REA's own open-source license grants no rights to the target. Do not claim all independently implemented functionality is necessarily forbidden either. Check the target license/authorization and relevant rights before an intended release; do not bypass access controls, license checks or technical protection to obtain material.
