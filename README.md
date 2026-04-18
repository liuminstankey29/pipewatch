# pipewatch

Lightweight CLI monitor for long-running data pipeline jobs with Slack alerting.

---

## Installation

```bash
pip install pipewatch
```

Or install from source:

```bash
git clone https://github.com/yourname/pipewatch.git && cd pipewatch && pip install .
```

---

## Usage

Wrap any pipeline command with `pipewatch` to monitor it and receive Slack alerts on completion or failure.

```bash
pipewatch --slack-webhook https://hooks.slack.com/services/XXX \
          --job-name "nightly_etl" \
          -- python run_pipeline.py --date 2024-01-15
```

pipewatch will:
- Track runtime and exit status of the wrapped process
- Send a Slack notification when the job finishes or crashes
- Print a live summary to stdout

### Configuration via environment variables

```bash
export PIPEWATCH_SLACK_WEBHOOK="https://hooks.slack.com/services/XXX"
export PIPEWATCH_JOB_NAME="my_pipeline"

pipewatch -- python run_pipeline.py
```

### Options

| Flag | Description |
|------|-------------|
| `--job-name` | Human-readable name shown in alerts |
| `--slack-webhook` | Incoming webhook URL for Slack |
| `--timeout` | Kill job and alert after N seconds |
| `--quiet` | Suppress stdout passthrough |

---

## License

MIT © 2024 Your Name