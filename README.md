# RCE Words Scraper

Scrape all the words that RCE has ever said.

supported platforms:
- Youtube (via generated transcripts)


This is super hacky, and just dumps a tonne of JSON files.
You'd best learn your grep-fu at this stage.


## Running

_Sorry, rough instructions as I'm typing them up as I leave the machine_

- Setup your Google API Key for accessing the Youtube Data API V3
- store it in a file called `.env` (basic structure shown in `example.env.FAKE`)
- setup the environment (`poetry install`)
- run the code, and watch the files pour into the `.rce-cache` directory (`poetry run ./run.py`)


## Do not be evil

Downloading everything that someone has said is fine, and we're doing it with good intentions here.

But it's also abusable.
Please don't be evil.

This is for fun only; and maybe to do some weird games in the channel.

