# Cryptomining Playbook

## Summary
When cryptomining activity is detected (high CPU, known mining tools like xmrig, outbound mining pool connections), the goal is to immediately kill the process and isolate the host.

## Approved Actions
1. **isolate_host**: Quarantine the infected worker node/host from the network. (Risk: High)
2. **kill_process**: Terminate the offending cryptomining process (e.g. xmrig). (Risk: Medium)
3. **block_ip**: Block the outbound destination IP of the mining pool. (Risk: Low)

## Rollback
- `isolate_host`: Restore host network connectivity.
- `block_ip`: Unblock the mining pool IP (not recommended).
