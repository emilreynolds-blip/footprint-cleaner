# Footprint Cleaner

A local Windows desktop case manager for discovering, documenting, and pursuing removal of old accounts and exposed personal information.

## What it does

- Maintains a local cleanup inventory and protected `KEEP` list.
- Seeds the known Facebook, Instagram, WhatsApp, Viber, and LinkedIn cases.
- Opens Google/Bing discovery searches and official platform recovery/privacy routes.
- Generates ownership-verification and deletion-request letters.
- Tracks status and exports an audit CSV.
- Refuses removal actions for protected entries.

## Important limitation

The application does not bypass passwords, multi-factor authentication, CAPTCHAs, identity checks, or platform security. For an inaccessible account it prepares and tracks the legitimate recovery, identity-verification, privacy-request, and escalation process. The account provider makes the deletion decision.

## Build on Windows 10/11 x64

Install Python 3.12, then run `build_windows.ps1`. This creates `dist\FootprintCleaner.exe`. Install Inno Setup 6 and compile `installer.iss` to create the installer.

The included GitHub Actions workflow produces `FootprintCleaner-Setup-0.1.0.exe` as a downloadable build artifact.

## Data location

The SQLite case database is stored at `%LOCALAPPDATA%\FootprintCleaner\footprint.db`. Do not enter passwords, recovery codes, government ID images, full dates of birth, or SSNs.
