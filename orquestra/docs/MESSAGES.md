# Noninterrupting messages

`enviar_space <pane> "message" [max_seconds=600]` queues ordinary notices when the agent is working. It checks the visible ANSI input area twice, ignoring dim suggestions. Typed input or an unrecognized screen is never submitted over. Unknown screen layouts fail closed. Pending files live in `ORCHESTRA_STATE/recados_pendentes`.

Run `entregar_pendentes` every two minutes. A single consumer groups queued notices per idle/done pane, oldest first, and deletes them only after successful delivery. `NAO_GUARDAR=1` means the caller will retry and must receive failure rather than a queued-success response. `URGENTE=1` bypasses the working-state delay only for protection/lifecycle requests; it still checks input. Return codes: 0 delivered or queued, 2 input unavailable, 3 working with caller-owned retry. These acknowledgements are not proof the model completed the requested task. Delivery is at-least-once across crashes, not exactly-once.

`pane_coordenador` is the generic replacement for the deployment-specific coordinator lookup: configure `ORCHESTRA_COORDINATOR`. New scripts honor `HERDR_BIN`. Existing Python tools keep their conservative idle checks. No routine job acknowledgement should wake the coordinator. Screen-parser changes require a fixture test before upgrading the terminal client.
