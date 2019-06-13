
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
--output_directory, -o  \n\trecords to selected destination         \n\t./beeye.py -o /Volumes/Disk1/trotlfolder\n
--stop_time, -s         \n\tterminates recording at selected time   \n\t./beeye.py -s 01:30:20  stops in 1h 30 min 20s\n
--farbe, -f             \n\trecord and display in color             \n\t./beeye.py -f \n
--remote, -r            \n\tactivate remote connection to wind tunnel
--audio, -a             \n\tactivates audio recording on selected channel \n\t./beeye.py -a 0   records from audio channel 0\n
--srate, -sr            \n\tsets sound sample rate                  \n\t./beeye.py -sr 16000    samples at 16 kHz. \n\tDefault is 48000\n
--frate, -fps           \n\tsets frame rate                         \n\t./beeye.py -fps 30      \n\tDefault is 20\n
--camera, -c            \n\tselect camera search range              \n\t./beeye.py -c 0 1 2 5   \n\tDefault is 0\n
'''
