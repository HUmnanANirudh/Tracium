# Possible Exfiltration Playbook

## Summary
Large data transfers or unauthorized outbound connections suggest potential data exfiltration.

## Approved Actions
1. **block_ip**: Block the destination IP address of the data transfer. (Risk: Medium)
2. **isolate_service**: Isolate the service originating the transfer. (Risk: High)
3. **disable_user**: Suspend the user session initiating the transfer. (Risk: Medium)

## Rollback
- `block_ip`: Remove the destination IP from the blocklist.
- `isolate_service`: Restore normal network policies for the service.
- `disable_user`: Re-enable the user session.
