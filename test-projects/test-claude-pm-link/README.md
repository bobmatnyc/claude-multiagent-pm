# Testing Claude PM Local Link

This project demonstrates how to use a locally linked version of Claude PM framework.

## Setup

1. The Claude PM framework has been linked globally from the development directory
2. This test project can now use the local development version

## Usage

```bash
# Initialize Claude PM in this project
claude-pm init

# Use Claude PM commands
claude-pm --version
claude-pm --help

# The CLI now uses the development version from:
# /Users/masa/Projects/claude-multiagent-pm
```

## Verification

The linked package points to the local development directory:
- Global link: `@bobmatnyc/claude-multiagent-pm@0.9.3 -> /Users/masa/Projects/claude-multiagent-pm`
- Any changes made in the development directory are immediately available

## Development Workflow

1. Make changes in `/Users/masa/Projects/claude-multiagent-pm`
2. Test immediately in any project using `claude-pm` commands
3. No need to rebuild or republish for testing

## Unlinking

To remove the local link and return to the published version:
```bash
# From any directory
npm unlink -g @bobmatnyc/claude-multiagent-pm

# Then install the published version
npm install -g @bobmatnyc/claude-multiagent-pm
```