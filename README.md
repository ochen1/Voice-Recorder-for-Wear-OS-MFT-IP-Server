# Voice Recorder for Wear OS MFT IP Server
Reverse-engineered minimal implmentation for "MFT IP Server" feature used by Voice Recorder for Wear OS (`pl.mobimax.voicerecorder`).

**⚠️ Warning: This script is not maintained. Its only purpose is to recover a single file that I needed, and it's "minimal" in the sense that it doesn't even send a completion indicator to the watch. Use with proper sandboxing. Use at your own risk.**

Script developed through man-in-the-middle TCP interception using socat: \
`socat -v -x TCP-LISTEN:60010 TCP:10.0.0.105:60010 &> traffic_hex.txt`

This network capture mini-project also doubles as a security audit. Very nice app, although it transmits potentially-sensitive data in plaintext TCP. Don't use this feature on public WiFi. There seems to be some hints in the app suggesting the data is transmitted in plaintext, but this may not be sufficient to warn the average non-technical user of this potential security concern.

Overall, good app. Thank you, developers!

## Background

One of my old smartwatches had an important voice recording stuck in the `pl.mobimax.voicerecorder` app's data directory. Here's what I tried to retrieve it.
1. `adb shell` and `run-as pl.mobimax.voicerecorder` - didn't have access, and app wasn't marked as debuggable. The watch isn't rooted.
2. `adb backup pl.mobimax.voicerecorder` - didn't work, seems to be deprecated.
3. This custom "MPT IP Server" implmentation - was able to successfully recover my files!

I'm still not sure what the root cause was, but I've already extracted all that I needed from my old watch. I believe it is due to a version mismatch between the watch & companion apps. Weirdly enough, the app version on my watch is 1.0.30, but my phone's companion app has version 1.0.26, which is also the latest version according to the Google Play Store. So I'm not too sure where 1.0.30 came from.

Today's Date: 2025-07-23

## Usage
Attached sample log output from when I used it to retrieve a recording:

```
[*] Listening on 0.0.0.0:60010...
[+] Connection from 10.0.0.151:57411
[*] Waiting for client handshake...
[*] Received handshake from: Samsung SM-R930 (packet size: 1024)
[*] Sending our handshake response...
[+] Handshake complete.
[*] Waiting for file metadata...
[*] Receiving file: Rec_162021_20250723.mp3 (3476609 bytes)
[+] Acknowledged metadata. Starting download...
[*] Progress: 3476609/3476609 bytes (100.00%)
[+] File download complete!
[-] Connection with 10.0.0.151 closed.
^C
[*] Shutting down server.
```
