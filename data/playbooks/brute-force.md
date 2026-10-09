# Brute Force Playbook

## Summary
When multiple failed login attempts are detected from a single IP, the primary goal is to prevent credential stuffing and account takeover.

## Approved Actions
1. **block_ip**: Block the source IP address if it is not an internal or known safe IP. (Risk: Low)
2. **disable_user**: If the account shows successful login after brute force, disable the user account to prevent further access. (Risk: High)
3. **notify**: Alert the user of suspicious activity. (Risk: Low)

## Rollback
- `block_ip`: Remove the IP from the firewall blocklist.
- `disable_user`: Re-enable the user account in the identity provider.
