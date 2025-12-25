# Systemd Error Log Checker

A simple script to quickly review and summarize recent systemd errors.

## Installation

1. Download the script:
   ```bash
   # Script is located at: check-systemd-errors
   ```

2. Make it executable:
   ```bash
   chmod +x check-systemd-errors
   ```

3. Move to ~/.local/bin/ (if not already in PATH):
   ```bash
   mv check-systemd-errors ~/.local/bin/
   ```

4. (Optional) Move to system-wide location:
   ```bash
   sudo mv check-systemd-errors /usr/local/bin/
   ```

**Note:** Following Unix convention, the .sh extension is removed for scripts in ~/.local/bin/.
The shebang line determines how the script executes, not the file extension.

## Usage

### Basic Usage

```bash
check-systemd-errors
```

Shows all error-level logs from the past hour.

### Specify Time Period

```bash
check-systemd-errors [time-period]
```

**Examples:**

```bash
# Last 30 minutes
check-systemd-errors "30 minutes ago"

# Since midnight today
check-systemd-errors "today"

# Last 24 hours
check-systemd-errors "24 hours ago"

# Specific date
check-systemd-errors "2025-12-17"

# Since specific time
check-systemd-errors "2025-12-18 08:00:00"
```

## Output Format

The script provides two sections:

### 1. Full Error Logs
Displays complete error messages in reverse chronological order (newest first), including:
- Timestamp
- Service/unit name
- Full error message

### 2. Error Summary
Shows the top 10 most frequently occurring errors with their count, helping identify recurring issues.

## What Errors Are Shown

The script filters for systemd log entries with priority levels:
- **Error** (3)
- **Critical** (2)
- **Alert** (1)
- **Emergency** (0)

Lower severity messages (warning, notice, info, debug) are excluded.

## Requirements

- systemd-based Linux distribution
- `journalctl` command (part of systemd)
- Bash shell

## Permissions

No special permissions required for viewing logs from:
- Current user's services
- System logs (depending on system configuration)

Use `sudo` if you need access to all system logs:
```bash
sudo check-systemd-errors
```

## Troubleshooting

**No output:** No errors found in the specified time period (this is good!)

**Permission denied:** Use `sudo` to access system-wide logs

**Invalid time format:** Use formats like "1 hour ago", "today", or "YYYY-MM-DD"

## Advanced Usage

### Combine with grep for specific services

```bash
check-systemd-errors | grep nginx
```

### Save output to file

```bash
check-systemd-errors "today" > errors-today.log
```

### Check specific service errors

```bash
journalctl -u nginx.service --since "1 hour ago" --priority=err
```
