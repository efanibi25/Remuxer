How to use quick
0. 
Create a BDMV: This will need to be done outside of this program
1. Call the Demux Command
    - remux.py --demux inpath
    - Program will Demux all Tracks for main playlist Audio,Subtitiles,Video
    - It will extract forced Subtitiles
    - You will find the outputted files in the same parent directory of the input BDMV
    - Format of output directory is mux.{random}.{title}
2. Optional Feature: JSON output
    - Currently Engish will be the default Track
    - If you want to change the order of tracks, or remove certain ones then edit the JSON File
    - You can do other tasks like changing the title of a tracks
    - Do not change the file names unless you know what your doing, as that will break the remux command
3. Call Remux
   - remux.py --remux inpath
   - point to the directory that you want to process which again will be mux.{random}.{title}
   - Will create a mkv in the path provided
 


Requirements
- To come
- You need fd:https://github.com/sharkdp/fd




Upcoming Changes
-Allow for more Default Languages
- More Options for Overall ease of Excluding or including of languages
-Switch to YAML for increase readabilitly 
- Try to increase user-friendlyness

