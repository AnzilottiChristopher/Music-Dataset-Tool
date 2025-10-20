# This will take flac files and convert them to wav files which is much better for us to work with
# ensure you have ffmpeg installed on your machine to get this to work

shopt -s nullglob

INPUT_DIR="./Music/flac_files"
OUTPUT_DIR="./Music/wav_files"

# ensure output directory exists
mkdir -p "$OUTPUT_DIR"

for f in "$INPUT_DIR"/*.[fF][lL][aA][cC]; do
  filename=$(basename -- "$f")
  wav="$OUTPUT_DIR/${filename%.*}.wav"

  if [[ -f "$wav" ]]; then
    echo "Skipping $filename (already exists)"
    continue
  fi

  echo "Converting $filename -> $(basename -- "$wav")"
  ffmpeg -i "$f" -c:a pcm_s24le "$wav"
done
