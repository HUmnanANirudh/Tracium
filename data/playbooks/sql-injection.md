# SQL Injection Playbook

## Summary
When a SQL injection attack is detected via WAF alerts or database syntax errors, the goal is to block the attacker and isolate the affected service.

## Approved Actions
1. **block_ip**: Block the source IP address of the attacker. (Risk: Low)
2. **isolate_container**: Isolate the database or frontend container to prevent lateral movement. (Risk: High)
3. **notify**: Alert the security operations center. (Risk: Low)

## Rollback
- `block_ip`: Remove the IP from the WAF/firewall blocklist.
- `isolate_container`: Restore network access to the container.
