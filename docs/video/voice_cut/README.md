# Blind Spot demo, voice-over cut (brag + Hyperframes + Kokoro)

`../blindspot_demo_voice.mp4` is the brag/Hyperframes cut (`../brag_cut/`) with an AI narration added and every scene and subtitle retimed to that narration. It was made by Claude Code on 15 Nov 2026 following brag's `--voice` path (Kokoro TTS through Hyperframes, run locally; no cloud TTS).

- **Narration:** the voice-over line of `docs/VIDEO_SCRIPT.md`, word for word (`narration-script.txt`). Kokoro voice `af_heart` (American English, female, a stock Kokoro voice, not a clone of anyone), speed 1.15. The final MP4 measures -16.1 LUFS integrated, peak -3.6 dBFS (ffmpeg ebur128). File: `composition/assets/narration.wav` (mono, 24 kHz, 16-bit, 29.7 s).
- **Subtitles:** the same words as written in the script, each group on screen while its own narration clip plays (`compositions/captions.html`).
- **Pictures:** the same real screenshots of the live app as the brag cut; nothing is redrawn.
- **No music, no SFX, no AI images.**
- **AI disclosure:** the note on every frame reads "Real screens from the live app · video assembled with AI (Claude Code, brag, Hyperframes) · AI voice (Kokoro) · no AI images". The MP4 also carries the metadata comment "Video assembled with AI (Claude Code, brag, Hyperframes). Narration is AI-generated speech (Kokoro TTS)."
- **Changed from the brag cut:** retimed to the narration (29.7 s); the end card is shorter (about 4.2 s); the ring around "1.94×" now encloses the whole figure; the AI note text.

If this cut is submitted, list the AI voice in the "Use of Super Intelligence (SI)" answer.

## Tools and versions

| Tool | Version | Licence |
|---|---|---|
| Hyperframes CLI (`npx hyperframes`, `tts`, `check`, `render`) | 0.9.52 | see the npm package |
| Kokoro-82M model, `kokoro-v1.0.onnx` + `voices-v1.0.bin` (model-files-v1.0 release of thewh1teagle/kokoro-onnx, downloaded by Hyperframes to `~/.cache/hyperframes/tts/models/`) | v1.0 | Apache-2.0 (hexgrad/Kokoro-82M) |
| kokoro-onnx (Python, used by `hyperframes tts`) | 0.6.1 | MIT |
| onnxruntime / phonemizer / espeakng-loader / soundfile | 1.32.0 / 3.6.0 / 0.2.4 / 0.14.0 | MIT / GPL-3.0 / no licence in package metadata, bundles espeak-ng (GPL-3.0) / BSD-3 |
| Python (venv for the TTS step) | 3.13.5 | |
| GSAP (vendored) | 3.15.0 | GSAP standard licence |
| Node.js / FFmpeg | 24.3.0 / 9.0.1 | |

Model weights are not stored here.

## Rebuild

From a scratch folder outside the repo:

    npm i hyperframes@0.9.52
    python -m venv kvenv && kvenv/Scripts/python -m pip install kokoro-onnx soundfile
    export HYPERFRAMES_PYTHON=$PWD/kvenv/Scripts/python.exe

    # 1. one clip per subtitle line (lines 1-9 of narration-script.txt), then trim edge silence
    npx hyperframes tts "<line>" --voice af_heart --speed 1.15 -o c1.wav     # ... c9.wav
    ffmpeg -i c1.wav -af "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.02,areverse,silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.05,areverse" t1.wav
    # 2. place clip i at the start time in narration-script.txt on a 29.7 s silent track (24 kHz mono),
    #    then two-pass loudnorm to I=-16, TP=-1.5 -> composition/assets/narration.wav
    # 3. render
    cp -r <repo>/docs/video/voice_cut/composition ./composition && cd composition
    npx hyperframes check
    npx hyperframes render --quality high -o ../voice_render.mp4 && cd ..
    # 4. poster as frame 0 + AAC + metadata
    ffmpeg -ss 2.0 -i voice_render.mp4 -frames:v 1 -q:v 2 poster.jpg
    #    (-3 dB: Hyperframes puts the mono narration on both stereo channels, which reads 3 LU louder)
    ffmpeg -i voice_render.mp4 -i poster.jpg -filter_complex "[0:v][1:v]overlay=0:0:enable='eq(n,0)'[v];[0:a]volume=-3.0dB[a]" \
      -map "[v]" -map "[a]" -c:v libx264 -crf 16 -preset slow -pix_fmt yuv420p -r 30 -c:a aac -b:a 160k \
      -metadata comment="Video assembled with AI (Claude Code, brag, Hyperframes). Narration is AI-generated speech (Kokoro TTS)." \
      -movflags +faststart blindspot_demo_voice.mp4
    ffprobe -v error -show_entries format=duration -of csv=p=0 blindspot_demo_voice.mp4   # must be <= 30.0
