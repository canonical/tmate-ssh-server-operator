# Changelog

This changelog documents user-relevant changes to the tmate SSH server charm.

## 2026-10-05

### Fixed

- Refresh the tmate server image and require patched `setuptools` and `wheel` in the charm.
- Restart the workload on charm upgrade so existing units receive the refreshed image.

## 2025-12-17

- Moved charm-architecture.md from Explanation to Reference category.

## 2025-10-28

- Added docs on how to upgrade the charm.

## 2025-10-14

- Fixed the charm status not reflecting errors with starting the tmate SSH daemon.

## 2025-08-20

- Added changelog to track user relevant changes.
