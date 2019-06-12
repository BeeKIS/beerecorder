
doc = '''
beeRecorder 1.2
====================
Program can record video with multiple cameras, both webcams or built-ins, industrial
like PointGrey.

There is also a possibility of remotely connecting to another system, for example an RPi via socks.
'''
details = '''
Keyboard Shortcuts:
to be added


== OPTIONS ==
"--output_directory", "-o"      records to selected destination         ./beeye.py -o /Volumes/Disk1/trotlfolder
"--stop_time", "-s"             terminates recording at selected time   ./beeye.py -s 01:30:20  stops in 1h 30 min 20s
"--farbe", "-f"                 record and display in color             ./beeye.py -f     records in camera
"--selected_cameras", "-k"      activate selected cameras only.         ./beeye.py -k 012 activates cameras 0, 1 and 2
"--remote", "-r"                activate remote connection to wind tunnel
"--audio", "-a"                 activates audio recording via selected channel ./beeye.py -a 0 records from audio channel 0
"--srate", "-sr"                sets sound sample rate                  ./beeye.py -sr 16000 samples at 16 kHz. Default is 48000
"--frate", "-fps"               sets frame rate                         ./beeye.py -fps 30 Default is 20
'''
