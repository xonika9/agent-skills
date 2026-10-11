# Models

Read this when the user wants a different accuracy, speed, or language trade-off than the default.

## Default

`ggml-large-v3-turbo-q8_0.bin` (whisper.cpp, about 874 MB) with the Silero voice-activity model. The voice-activity pass keeps Whisper from inventing text in silence and music-only stretches.

## Another Whisper model

`run --model <file>` accepts any ggml Whisper model; the official files are listed in the `ggerganov/whisper.cpp` repository on Hugging Face. Download a model only after the user chooses it, into the models directory used by `check`. Larger is not automatically better: `large-v3` (tested as `q5_0`) is several times slower than turbo and, in the comparison below, also repeated a phrase and dropped speech under music.

Existing outputs stay current until their source changes, so applying a new model to already transcribed files needs `--force`.

## Engines this script does not run

GigaAM-v3 (Russian only) and NVIDIA Parakeet v3 are faster than Whisper turbo but need their own runtimes and produce different segment layouts. Treat a request for them as a separate change to the script rather than an option.

## One measured comparison

A single comparison, not a benchmark to rely on: two Russian videos (a 12-minute narrated game-lore video with many proper names and a 20-minute vlog), Apple M4 Pro, October 2026. Error rates come from 1,120 words of hand-adjudicated reference text.

| Model | Word error rate | Speed vs real time | Notes |
| --- | --- | --- | --- |
| Whisper large-v3-turbo q8_0 | 2.6% | ~21× | Most consistent across both videos |
| GigaAM-v3 e2e-ctc (CPU) | 2.8% | ~36–50× | Mixes Latin and Cyrillic in English names |
| Whisper large-v3 q5_0 | 2.9% | ~7.5× | Best proper-name spelling; repeated a phrase, dropped speech under music |
| GigaAM-v3 e2e-rnnt (CPU) | 3.8% | ~35× | |
| Parakeet-TDT-0.6b-v3 (MLX) | 5.8% | ~57× | Most precise timestamps; more grammar and name errors |

Re-measure on the user's own recordings before changing the default; accent, microphone, and vocabulary move these numbers.
