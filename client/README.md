## Summary

This is a harness for Minecraft that connects to a Minecraft server, tests policies, and records "state-action" logs in a transitions pool.


## Bot Goal

The bot targets the nearest dropped item within `RANGE`, keeps that item as its target until it is collected or disappears, and selects another nearby item afterward. When there is no active item in range, the environment chooses `noop` without invoking the policy.