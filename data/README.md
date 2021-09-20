Download data

```bash
# https://www.youtube.com/watch?v=fQf_12r_Z8I By Piece of French

VIDEO_ID="fQf_12r_Z8I"
NAME="ex01"

# info.json of youtube-dl
youtube-dl -j "$VIDEO_ID" | jq > "$NAME.info.json"

# .ttml subtitle files
youtube-dl -o "$NAME.%(ext)s" --skip-download --write-sub --write-auto-sub --sub-lang=fr,en --sub-format=ttml "$VIDEO_ID"

# Youtube html page
curl -H "accept-language: en" "https://www.youtube.com/watch?v=$VIDEO_ID" > "$NAME.html"

# "player response" json
python -c "import re; print(re.search('var ytInitialPlayerResponse = ({.+?});', open('$VIDEO_ID.html').read()).group(1))" | jq > "$NAME.player-response.json"
```

Convert ttml to json

```bash
python demo/misc/ttml_to_json.py < data/ex01.fr.ttml > data/ex01.fr.ttml.json
python demo/misc/ttml_to_json.py < data/ex01.en.ttml > data/ex01.en.ttml.json
```
