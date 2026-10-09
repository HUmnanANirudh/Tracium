# Suspicious Shell Playbook

## Summary
Execution of unexpected shell commands indicates potential remote code execution or unauthorized access.

## Approved Actions
1. **isolate_service**: Isolate the affected container or service from the network. (Risk: High)
2. **disable_user**: Disable the user account associated with the command execution. (Risk: High)
3. **notify**: Alert the security operations center immediately. (Risk: Low)

## Rollback
- `isolate_service`: Restore network routing to the container.
- `disable_user`: Re-enable the user account in the identity provider.
