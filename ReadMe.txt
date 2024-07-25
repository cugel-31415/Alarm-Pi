Alarm Pi
========

This is a project that can turn a Raspberry Pi computer into an alarm clock. It needs a few additional items:
	- A realtime clock module (I'm using an AZDelivery DS1302)
	- An LCD display (I'm using a 16 x 2 characters display from AZDelivery, it also needs an I2C adapter and logic level converter)
	- A power amplifier (I'm using a DollaTek 10 Watt mini hifi-stereo board)
	- Two speakers
	- 12 Volt power adapter for the amplifier
	- 5 Volt power adapter for the Raspberry Pi
	- Relais module for turning the power amplifier on and off
	- 3 momentary switches
	- Wiring (I used jumper wire which makes assembly somewhat easier. Some soldering is required still)


The idea for the project arose when my old alarm clock started acting up. My old alarm clock was one that was equipped with a CD
player. When the alarm went off, the CD started playing, waking me with music instead of annoying beeps or what-have-you.
I liked that.
But for the last few years the CD player started having problems. Many CD's it would not play very well, constantly hickupping and
losing the correct playback position. Then it would have to search for a few seconds before continuing. Still preferable to beeping
but not by much.

There were other issues with the setup. There was the fact that I was too lazy to replace the CD regularly, resulting in listening
to the same CD for months on end. And always in the same order as there was no random mode.
The CD, if it played correctly, would play for 1 hour exactly and then end abruptly. If the CD was shorter than 1 hour it would start
again at the beginning. If it was longer, I never got to hear the music beyond the 1 hour limit.
I also had disconnected the two tiny speakers in the casing and instead rewired the outputs to real hifi speakers. That had improved
the sound considerably, but the way I had connected the speakers was incredibly primitive and made moving the thing a hassle.
After about 10 years of this routine I felt it was time for a change.

I got the idea to replace the CD player with a Raspberry Pi. I imagined connecting it somehow to the power supply lines that powered
the CD player and feed its sound into the built-in amplification of the alarm clock. After a week of experimentation I seemed to have
a setup that might work. Then disaster struck. I'm not exactly sure what went wrong, possibly it had to do with a large blob of solder
accidently falling on the pcb, but it stopped working. I tried to repair the damage but I failed and eventually I threw it in the trash.

Now being out of an alarm clock altogether, I frantically racked my brain for a solution. I looked online for something that could
replace my old alarm clock, but nothing appealed to me. I didn't want BlueTooth what most of them had. I didn't want wifi or other
nonsense either. Also I didn't trust that the devices could play the various sound file formats that are in my music library (ogg, flac). 
MP3 I trusted they would be able to handle, but that is not enough for me.

So I decided to do it myself. I had an old Raspberry Pi 1B lying around. I just finished a course in Python. What was going to stop me?
Nothing as it turned out. A week of pottering and the proto-type is on my night table.



Contents
========

The final result consists of a number of files of which I will give a short description here.

	alarm.py		The main executable. It is a python script. To run it, invoke python with the path to the script, e.g.
				python ./alarm.py (if you are in the same directory).
				I actually added it as a cron job so it runs automatically as the computer boots.
	
	alarm.ini		This file contains a few settings that are stored between sessions. It will be created if not present.


	LCDI2C_backpack.py	This is used for communicating with the LCD. If you're using a different display it will probably not
				work and you may need to make modifications

	pyRPiRTC.py		This is used for communicating with the realtime clock. The same restrictions apply as for the LCD.

	startup.mp3		This file will be played when the program starts. You can change it to something else if you want.

	sources.txt		This file contains the audio sources. It is a list of directories that contain audio files. You can
				think of them as CD's. Each directory contains 1 or more audio files that will be played as a whole.
				Within the alarm clock application one of these sources is selected. When the alarm triggers it will
				play the audio files in alphabetic order. When all files are played the alarm returns to the inactive 
				state.

				The first entry of the sources list contains the base directory. This is important. All the other
				directories are subdirectories of this base directory. The full path is created by appending the
				source to the base directory. It is recommended that the source has at least two nesting levels. The
				first level is the artist or band name, the second level an album title. However, you can leave out
				the second level if you don't need it.

	alarm.mp3		If the application does not find any sources, it will use this file and play it repeatedly until
				you turn off the alarm

	schematic.jpg		Image of how I connected the various components to the Raspberry Pi's GPIO pins.



Raspberry Pi Configuration
==========================
I installed Raspbian 'Jessie' on the Raspberry Pi. As this is an old version that is no longer supported it was a bit of a hassle, but
it is still possible. The initial installation comes from an image file that you write to an SD-card. The problems start when you want
to update or install extra's. The mirror servers are no longer valid and you need to manually configure them to look into legacy 
sources.
Installing vlc is absolutely required. The alarm clock application relies heavily on vlc to play the audio files.
Once you have solved the update issue you can use 'sudo apt-get install vlc'. That worked for me.
Python is also needed but it is already installed by default.
I configured the system to have a ram-disk where all the temp and var directories are pointing to. This way the system will do all
its logging to memory instead of to the SD-card. This will extend the life of the card but also, far more importantly, will greatly
reduce the risk of bricking the card in case of a power failure.

A few things need to be configured via raspi-config. Audio needs to be routed to the audio output socket (headphone), not HDMI.
I2C needs to be on, ethernet can be on which can be handy to transfer audio files to the SD-card. Note that in normal operation
networking is disabled. If you need ethernet access, go to the exit menu mode as described in the manual below.	
The system needs to boot in command line mode. No desktop is needed nor desired.



Manual
======

The application uses only 3 switches, two white switches named 'left' and 'right' and a red switch named 'command'. 
To still be able to do everything there are a few modes of operation that you can switch between. A switch can be pressed either 
short or long (held more than 3 seconds) which has a different effect. In some modes a button can be held and its action will repeat.
I will briefly describe the modes here, grouping them in functional blocks.

	inactive	By default the application is in inactive mode. The LCD backlight is off. Pressing any button for a short
			time will put the application in display mode. 
			Long pressing the 'command' button enters exit menu mode.

	display		In this mode the display is lit. It shows the current time, date and the alarm and random status. 

			If the display shows an 'R' after the date, random mode is on. Otherwise random mode is off.
			In random mode the player will play the audio files from a source in random order. If random mode
			is off, the files will be played in alphabetical order.

			If the display shows an 'A' after the time, the alarm is set. Otherwise the alarm is not set.

			Short pressing the 'left' button toggles the alarm on or off.
			Short pressing the 'right' button toggles the random mode on or off.
			Long pressing the 'left' button enters set alarm hour mode.
			Long pressing the 'right' button enters set time hour mode.
			Long pressing the 'command' button enters player mode.
			If no button is pressed for 10 seconds, the application goes back to inactive mode


	SET TIME AND DATE
____________________________________________________________________________________________________________
|
|	set time hour	In this mode the display shows the current time. The current hour can be changed.
|			Short pressing the 'command' button enters set time min mode.
|			Long pressing the 'command' button returns to display mode.
|			If no button is pressed for 10 seconds, the application goes back to inactive mode
|			
|	set time min	In this mode the display shows the current time. The current minute can be changed.
|			Short pressing the 'left' button decreases the minute. Holding will repeat.
|			Short pressing the 'right' button increases the minute. Holding will repeat.
|			Short pressing the 'command' button enters set date year mode.
|			Long pressing the 'command' button returns to display mode.
|			If no button is pressed for 10 seconds, the application goes back to inactive mode
|			
|	set date year	In this mode the display shows the current date. The current year can be changed.
|			Short pressing the 'left' button decreases the year. Holding will repeat.
|			Short pressing the 'right' button increases the year. Holding will repeat.
|			Short pressing the 'command' button enters set date month mode.
|			Long pressing the 'command' button returns to display mode.
|			If no button is pressed for 10 seconds, the application goes back to inactive mode
|			
|	set date month	In this mode the display shows the current date. The current month can be changed.
|			Short pressing the 'left' button decreases the month. Holding will repeat.
|			Short pressing the 'right' button increases the month. Holding will repeat.
|			Short pressing the 'command' button enters set date day mode.
|			Long pressing the 'command' button returns to display mode.
|			If no button is pressed for 10 seconds, the application goes back to inactive mode
|			
|	set date day	In this mode the display shows the current date. The current day can be changed.
|			Short pressing the 'left' button decreases the day. Holding will repeat.
|			Short pressing the 'right' button increases the day. Holding will repeat.
|			Short pressing the 'command' button enters set time hour mode.
|			Long pressing the 'command' button returns to display mode.
|			If no button is pressed for 10 seconds, the application goes back to inactive mode
------------------------------------------------------------------------------------------------------------


	SET ALARM
____________________________________________________________________________________________________________
|
|	set alarm hour	In this mode the display shows the alarm time. The alarm hour can be changed.
|			Short pressing the 'left' button decreases the alarm hour. Holding will repeat.
|			Short pressing the 'right' button increases the alarm hour. Holding will repeat.
|			Short pressing the 'command' button enters set alarm  min mode.
|			Long pressing the 'command' button returns to display mode.
|			If no button is pressed for 10 seconds, the application goes back to inactive mode
|			
|	set alarm min	In this mode the display shows the alarm time. The alarm minute can be changed.
|			Short pressing the 'left' button decreases the alarm minute. Holding will repeat.
|			Short pressing the 'right' button increases the alarm minute. Holding will repeat.
|			Short pressing the 'command' button enters set alarm hour mode.
|			Long pressing the 'command' button returns to display mode.
|			If no button is pressed for 10 seconds, the application goes back to inactive mode
------------------------------------------------------------------------------------------------------------


	AUDIO PLAYER
____________________________________________________________________________________________________________
|
|	player		In this mode playback of the selected source starts. When the alarm goes off, this
|			mode is entered automatically, but it can also be entered at other times, just to 
|			listen to music.
|			The audio files in the source directory will be played in alphabetic order, one by
|			one, until all have been played. You can use a two digit number at the start of the
|			file name to make sure they will be played in a specific order. For example:
|				01 First Track.mp3
|				02 Second Track.mp3
|
|			If random mode is active, the files will be played in random order.			
|
|			While playing, the display backlight remains on and the application will stay in this
|			mode until the user exits it.
|			The display shows the selected source and the currently playing track as a two digit
|			number. The display also shows the current time and an 'A' if the alarm is set.
|			If the player mode was entered because the alarm went off, the display shows two hash tags '##'
|			after the alarm indicator.
|
|			Short pressing the 'left' button moves playback to the previous track. Holding will repeat.
|			Short pressing the 'right' button moves playback to the next track. Holding will repeat.
|			Short pressing the 'command' button exits player mode and returns to inactive mode.
|			Long pressing the 'command' button enters select source mode.
|			
|	select source	In this mode a source can be selected. The display shows the first two nesting levels
|			of the source on two lines. Depending on how the source is structured this could be
|			the artist name on the first line and the album name on the second line.
|
|			Short pressing the 'left' button selects the previous source. Holding will repeat.
|			Short pressing the 'right' button selects the next source. Holding will repeat.
|			Short pressing the 'command' button returns to player mode. The selected source will start playing.
------------------------------------------------------------------------------------------------------------


	EXIT
____________________________________________________________________________________________________________
|
|	exit menu	This mode allows you to either terminate the application or shutdown the system. Terminating the application
|			is probably not useful for the average user. It is implemented for development
|			Shutting down the system via the menu is safer than just pulling the power plug which can lead to sd-card 
|			failure. 
|			In general the application will always be on and a shutdown will never be needed.
|			Additionally when the application is in exit menu mode, USB power and network are turned on. In normal
|			operation these are turned off to reduce power consumption.
|
|			After shutdown, either intentional or accidental, remove the powerplug from the socket. The Raspberry Pi still 
|			uses power after shutdown so this will save some electricity. It is also the only way to boot the system again 
|			(by reinserting the power plug) if the shutdown was intentional. If there was an accidental power failure the
|			system will of course boot automatically when power is resumed.
|
|			The menu shows three options 'Cncl' (left button), 'Exit' (right button) and 'POff' (command button)
|			Short pressing the 'left' button returns to inactive mode without doing anything.
|			Long pressing the 'right' button terminates the application.
|			Long pressing the 'command' button shuts down the system.
------------------------------------------------------------------------------------------------------------








