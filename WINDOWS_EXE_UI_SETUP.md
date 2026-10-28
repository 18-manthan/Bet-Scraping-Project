# Windows EXE UI Setup

Use this guide when the client will run the bot from the desktop UI, without using terminal commands.

## What The Client Needs

- Windows laptop/desktop
- Google Chrome installed
- The final app file:

```text
LuckyNumbersBot.exe
```

- Excel/CSV betting input file

## Build The EXE

Build the `.exe` on a Windows system from the project folder:

```text
build_windows_exe.bat
```

After build, the final app will be created here:

```text
dist\LuckyNumbersBot.exe
```

## Give To Client

Give the client:

```text
LuckyNumbersBot.exe
```

The client can place it anywhere, for example:

```text
Desktop
Downloads
Documents
```

The app can be opened by double-clicking `LuckyNumbersBot.exe`.

Important: run result CSV files will be saved in the same folder where the `.exe` is placed.

## Daily Use Flow

1. Double-click `LuckyNumbersBot.exe`.
2. Click `Start Chrome`.
3. Complete Cloudflare verification if it appears.
4. Log in to Hollywoodbets manually.
5. In the app, select the Excel/CSV file using `Browse`.
6. Enter the stake amount.
7. Select run mode.
8. Select start row option.
9. Click `Start Bot`.
10. Watch progress in `Live Logs`.

## Recommended Client Mode

For one Excel row submitted as one Multiple bet:

```text
Run Mode: Real submit - Multiple row
Stake: 1
Start Rows: Start from beginning / Resume / Specific row
```

## Notes

- Chrome must stay open while the bot is running.
- If Cloudflare appears, complete it manually. The bot will wait and continue.
- If login is not complete, the bot will wait for manual login.
- If the Excel file is changed, select the updated file again using `Browse`.
- If the `.exe` is moved to another folder, it will still open, but new result files will be saved in that new folder.

