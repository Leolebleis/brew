# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

HTTP API that wraps the Fellow Aiden cloud API, self-hosted on a Raspberry Pi. Surfaces brew profiles, schedules, and device settings over a local network endpoint.

## Architecture

- Proxies requests to Fellow's cloud API (`https://l8qtmnc692.execute-api.us-west-2.amazonaws.com/v1`)
- Auth: Fellow email/password -> JWT Bearer tokens (~15min expiry)
- Core library: `fellow-aiden` ([9b/fellow-aiden](https://github.com/9b/fellow-aiden))
- Deployed on Raspberry Pi 4 Model B

## Key Constraints

- Fellow cloud API only -- no local/LAN API exists
- Can manage profiles, schedules, and device settings; **cannot trigger a brew remotely**
- JWT tokens expire quickly (~15min) -- must handle refresh
- Aiden connects via 2.4 GHz WiFi only
