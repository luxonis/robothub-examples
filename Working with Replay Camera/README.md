1. First download videos using the following command:
   `python download.py`

2. create frames directory using the following command:

- move to the vids directory:
  `cd vids`

- create frames directory:
  `mkdir frames`

- get frames from the video:
  `ffmpeg -i vid1.mp4 frames/frame%04d.png`

3. run examples
