from LCDI2C_backpack import LCDI2C_backpack
import RPi.GPIO as GPIO
import time
import datetime
import pyRPiRTC
import os.path
import subprocess
import threading


INI_FILE = "alarm.ini"
SOURCES_FILE = "sources.txt"
ALARM_FILE = "alarm.mp3"
STARTUP_FILE = "startup.mp3"
dir_path = os.path.dirname(os.path.realpath(__file__))

sources_base_dir = ""
sources = []
tracks = []

LCD_WRITE_TIME_SEC = 0.15

SCAN_INTERVAL_MS = 100.0
SLEEP_TIME = SCAN_INTERVAL_MS / 1000.0

LONG_PRESS_SEC = 3.0
LONG_PRESS_COUNT = int((LONG_PRESS_SEC * 1000.0) / SCAN_INTERVAL_MS)

REPEAT_PRESS_SEC = 1.0
REPEAT_PRESS_COUNT = int((REPEAT_PRESS_SEC * 1000.0) / SCAN_INTERVAL_MS)

INACTIVITY_TIMEOUT_SEC = 10.0
INACTIVITY_TIMEOUT_COUNT = int((INACTIVITY_TIMEOUT_SEC * 1000.0) / SCAN_INTERVAL_MS)

PLAYER_TIMEOUT_SEC = 3.0
PLAYER_TIMEOUT_COUNT = int((PLAYER_TIMEOUT_SEC * 1000.0) / SCAN_INTERVAL_MS)

PLAYER_UPDATE_SEC = 1.0
PLAYER_UPDATE_COUNT = int((PLAYER_UPDATE_SEC * 1000.0) / SCAN_INTERVAL_MS)

# interval to check alarm trigger
UPDATE_TIME_SEC = 15.0
UPDATE_TIME_COUNT = int((UPDATE_TIME_SEC * 1000.0) / SCAN_INTERVAL_MS)

cur_mode = -1
cur_source = 0
cur_track = -1
update_count = UPDATE_TIME_COUNT
activity_count = 0
activity = False
time_hour = -1
time_min = -1
time_str = "00:00"
date_year = -1
date_month = -1
date_day = -1
date_str = "1 Jan 1970"
bRandom = False
str_random_state = "   "
bAlarm = False
str_alarm_state = "   "
bAlarmActive = False
alarm_hour = 0
alarm_min = 0
alarm_str = "00:00"
bSetClock = False
set_time_hour = 0
set_time_min = 0
set_time_str = "00:00"
set_date_year = 0
set_date_month = 0
set_date_day = 0
set_date_str = "1 Jan 1970"
step = 1
bWriteIni = False

class vlc_comm(object):
	bGoDown = False
	bStopped = True
	bNewTrack = False
	cur_track = ""

bPlayerActive = False
player_update_counter = 0


# name the f-ing indices, stupid snake!
MODE_IDX_OFF = 0
MODE_IDX_DISPLAY = 1
MODE_IDX_SET_ALARM_HOUR = 2
MODE_IDX_SET_ALARM_MIN = 3
MODE_IDX_SET_TIME_HOUR = 4
MODE_IDX_SET_TIME_MIN = 5
MODE_IDX_SET_DATE_YEAR = 6
MODE_IDX_SET_DATE_MONTH = 7
MODE_IDX_SET_DATE_DAY = 8
MODE_IDX_PLAYER = 9
MODE_IDX_SELECT_SOURCE = 10
MODE_IDX_EXIT = 11


MODE_NAME = 0
MODE_INITIALIZER = 1
MODE_BTN_ACTION = 2
MODE_BTN_REPEAT_ACTION = 3
MODE_BTN_LONG_ACTION = 4
MODE_BTN_INSTANT_ACTION = 5
MODE_NEXT = 6

BTN_NAME = 0
BTN_PIN = 1
BTN_STATE = 2
BTN_READ = 3
BTN_COUNTER = 4
BTN_LONG = 5
BTN_MODE = 6

RELAIS_1_PIN = 16
RELAIS_2_PIN = 18


# dummy function
def fnc_none():
	return



def fnc_relais(bOn):
	value = 1
	if bOn:
		value = 0

	GPIO.output(RELAIS_1_PIN, value)
	GPIO.output(RELAIS_2_PIN, value)



def fnc_test_relais():
	print("Relais 1 on")
	GPIO.output(RELAIS_1_PIN, 1)
	time.sleep(2)
	print("Relais 1 off")
	GPIO.output(RELAIS_1_PIN, 0)
	time.sleep(2)

	print("Relais 2 on")
	GPIO.output(RELAIS_2_PIN, 1)
	time.sleep(2)
	print("Relais 2 off")
	GPIO.output(RELAIS_2_PIN, 0)



def fnc_show_date():
	global date_str

	lcd.lcd_string(date_str, lcd.LCD_LINE_1)



def fnc_show_time():
	global time_str

	lcd.lcd_string(time_str, lcd.LCD_LINE_2)



def fnc_update_time(bForce = False):
	global time_str
	global time_hour
	global time_min
	global date_str
	global date_year
	global date_month
	global date_day
	global cur_mode
	global str_alarm_state
	global str_random_state
	global bAlarmActive

	now = rtc.read_datetime()

	bUpdate = False
	bUpdateDate = False

	if now.minute != time_min:
		time_min = now.minute
		bUpdate = True

		# hour only needs to be checked when minute changes
		if now.hour != time_hour:
			time_hour = now.hour
			bUpdate = True
		
			# date only needs to be checked when hour changes
			if now.year != date_year:
				date_year = now.year
				bUpdateDate = True
			if now.month != date_month:
				date_month = now.month
				bUpdateDate = True
			if now.day != date_day:
				date_day = now.day
				bUpdateDate = True
		
	if bUpdate or bForce:
		time_str = ""
		time_str = str(time_hour).zfill(2) + ":" + str(time_min).zfill(2) + "   " + str_alarm_state + str_random_state
		if (cur_mode == MODE_IDX_DISPLAY) or (cur_mode == MODE_IDX_PLAYER):
			fnc_show_time()
			if (cur_mode == MODE_IDX_DISPLAY) and (bForce or bUpdateDate):
				date_str = ""
				date_str = str(date_year).zfill(4) + "-" + str(date_month).zfill(2) + "-" + str(date_day).zfill(2)
				fnc_show_date()

			


def fnc_set_mode(new_mode):
	global cur_mode
	global activity_count

	if new_mode == cur_mode:
		return

	#show mode name
	cur_mode = new_mode
	lcd.lcd_string(modes[cur_mode][MODE_NAME], lcd.LCD_LINE_1)

	# call initializer
	modes[cur_mode][MODE_INITIALIZER]()

	activity_count = 0



# go to next mode and initialize it
def fnc_next_mode():
	global cur_mode
	global modes

	fnc_set_mode(modes[cur_mode][MODE_NEXT])



def fnc_update_all():
	global bSetClock
	global bWriteIni
	global time_hour
	global time_min
	global date_year
	global date_month
	global date_day
	global set_time_hour
	global set_time_min
	global set_date_year
	global set_date_month
	global set_date_day

	if bSetClock:
		bSetClock = False
		now = rtc.read_datetime()
		new_time = datetime.datetime(set_date_year, set_date_month, set_date_day, set_time_hour, set_time_min, 0, 0)
		rtc.write_datetime(new_time)

		time_hour = set_time_hour
		time_min = set_time_min
		date_year = set_date_year
		date_month = set_date_month
		date_day = set_date_day
		fnc_update_time(True)
	
	if bWriteIni:
		bWriteIni = False
		fnc_write_settings()



def fnc_init_light_off():
	lcd.backlight(False)
	lcd.clear()
	fnc_update_all()



def fnc_init_display():
	fnc_update_all()
	lcd.backlight(True)
	fnc_update_alarm_state()
	fnc_update_time(True)



def fnc_update_random_state():
	global str_random_state
	global bRandom

	str_random_state = "    "
	if bRandom:
		str_random_state = "   R"



def fnc_toggle_random():
	global bRandom
	global bWriteIni

	bRandom = not bRandom
	fnc_update_random_state()
	fnc_update_time(True)
	bWriteIni = True
	fnc_update_all()



def fnc_update_alarm_state():
	global str_alarm_state
	global bAlarm
	global bAlarmActive

	str_alarm_state = "    "
	if bAlarm:
		str_alarm_state = "A   "
		if bAlarmActive:
			str_alarm_state = "A ##"
		
	

def fnc_toggle_alarm():
	global bAlarm
	global bWriteIni

	bAlarm = not bAlarm
	fnc_update_alarm_state()
	fnc_update_time(True)
	bWriteIni = True
	fnc_update_all()



def fnc_set_fast():
	global step

	step = 2



def fnc_show_set_string(set_string):
	lcd.lcd_string(set_string, lcd.LCD_LINE_2)



def fnc_update_alarm():
	global alarm_hour
	global alarm_min
	global alarm_str

	alarm_str = str(alarm_hour).zfill(2) + ":" + str(alarm_min).zfill(2)
	fnc_show_set_string(alarm_str)
	


def fnc_init_set_alarm_hour():
	fnc_update_alarm()



def fnc_dec_alarm_hour():
	global alarm_hour
	global step
	global bWriteIni

	alarm_hour -= step
	if alarm_hour < 0:
		alarm_hour += 24

	fnc_update_alarm()
	bWriteIni = True


	
def fnc_inc_alarm_hour():
	global alarm_hour
	global step
	global bWriteIni

	alarm_hour += step
	if alarm_hour >= 24:
		alarm_hour -= 24
	
	fnc_update_alarm()
	bWriteIni = True


	
def fnc_init_set_alarm_min():
	fnc_update_alarm()



def fnc_dec_alarm_min():
	global alarm_min
	global step
	global bWriteIni

	alarm_min -= step
	if alarm_min < 0:
		alarm_min += 60

	fnc_update_alarm()
	bWriteIni = True


	
def fnc_inc_alarm_min():
	global alarm_min
	global step
	global bWriteIni

	alarm_min += step
	if alarm_min >= 60:
		alarm_min -= 60

	fnc_update_alarm()
	bWriteIni = True



def fnc_get_set_time_date():
	global time_hour
	global time_min
	global set_time_hour
	global set_time_min
	global date_year
	global date_month
	global date_day
	global set_date_year
	global set_date_month
	global set_date_day

	set_time_hour = time_hour
	set_time_min = time_min
	set_date_year = date_year
	set_date_month = date_month
	set_date_day = date_day



def fnc_update_set_time():
	global set_time_hour
	global set_time_min
	global set_time_str

	set_time_str = str(set_time_hour).zfill(2) + ":" + str(set_time_min).zfill(2)
	fnc_show_set_string(set_time_str)
	


def fnc_init_set_hour():
	fnc_update_set_time()



def fnc_dec_hour():
	global set_time_hour
	global step
	global bSetClock

	set_time_hour -= step
	if set_time_hour < 0:
		set_time_hour += 24

	fnc_update_set_time()
	bSetClock = True


	
def fnc_inc_hour():
	global set_time_hour
	global step
	global bSetClock

	set_time_hour += step
	if set_time_hour >= 24:
		set_time_hour -= 24
	
	fnc_update_set_time()
	bSetClock = True


	
def fnc_init_set_min():
	fnc_update_set_time()



def fnc_dec_min():
	global set_time_min
	global step
	global bSetClock

	set_time_min -= step
	if set_time_min < 0:
		set_time_min += 60

	fnc_update_set_time()
	bSetClock = True


	
def fnc_inc_min():
	global set_time_min
	global step
	global bSetClock

	set_time_min += step
	if set_time_min >= 60:
		set_time_min -= 60

	fnc_update_set_time()
	bSetClock = True



def fnc_get_limit_day():
	global set_date_year
	global set_date_month

	limit = 31
	if set_date_month in (2, 4, 6, 9, 11):
		limit = 30
		if set_date_month == 2:
			limit = 28
			if ((set_date_year % 4) == 0) and ((set_date_year % 100) != 0):
				limit = 29

	return limit



def fnc_update_set_date():
	global set_date_year
	global set_date_month
	global set_date_day
	global set_date_str
	global bSetClock

	limit = fnc_get_limit_day()
	if set_date_day > limit:
		bSetClock = True
		set_date_day = limit

	set_date_str = str(set_date_year).zfill(4) + "-" + str(set_date_month).zfill(2) + "-" + str(set_date_day).zfill(2)
	fnc_show_set_string(set_date_str)
	


def fnc_init_set_year():
	fnc_update_set_date()



def fnc_dec_year():
	global set_date_year
	global step
	global bSetClock

	set_date_year -= step
	if set_date_year < 2024:
		set_date_year = 2100

	fnc_update_set_date()
	bSetClock = True


	
def fnc_inc_year():
	global set_date_year
	global step
	global bSetClock

	set_date_year += step
	if set_date_year > 2100:
		set_date_year = 2024
	
	fnc_update_set_date()
	bSetClock = True


	
def fnc_init_set_month():
	fnc_update_set_date()



def fnc_dec_month():
	global set_date_month
	global step
	global bSetClock

	set_date_month -= step
	if set_date_month < 1:
		set_date_month = 12

	fnc_update_set_date()
	bSetClock = True


	
def fnc_inc_month():
	global set_date_month
	global step
	global bSetClock

	set_date_month += step
	if set_date_month > 12:
		set_date_month = 1
	
	fnc_update_set_date()
	bSetClock = True


	
def fnc_init_set_day():
	fnc_update_set_date()



def fnc_dec_day():
	global set_date_day
	global step
	global bSetClock

	limit = fnc_get_limit_day()

	set_date_day -= step
	if set_date_day < 1:
		set_date_day = limit

	fnc_update_set_date()
	bSetClock = True


	
def fnc_inc_day():
	global set_date_day
	global step
	global bSetClock

	limit = fnc_get_limit_day()

	set_date_day += step
	if set_date_day > limit:
		set_date_day = 1
	
	fnc_update_set_date()
	bSetClock = True


	
def thrd_read_vlc(vlc, bNonsense):
	global vlc_if
	
	CMD_PLAY = "( state playing )"
	CMD_STOP = "( state stopped )"
	CMD_NEW_FILE = "> ( new input: file://"
	new_track = ""

	while not vlc_if.bGoDown:
		line = vlc.stdout.readline()

		if line[:len(CMD_STOP)] == CMD_STOP:
			if not vlc_if.bStopped:
				vlc_if.bStopped = True
#				print("VLC PLAYBACK HAS STOPPED")
		elif line[:len(CMD_PLAY)] == CMD_PLAY:
			if vlc_if.bStopped:
				vlc_if.bStopped = False
#				print("VLC PLAYBACK HAS STARTED")
		elif line[:len(CMD_NEW_FILE)] == CMD_NEW_FILE:
			new_track = line[len(CMD_NEW_FILE):-4]
			if vlc_if.cur_track != new_track:
				vlc_if.cur_track = new_track
				vlc_if.bNewTrack = True
#				print("VLC NEW FILE: " + new_track)
			


def fnc_open_source():
	global cur_source
	global cur_track
	global sources
	global tracks
	global vlc
	global vlc_if

	vlc.stdin.write("stop\n")

	# clear playlist
	cur_track = -1
	del tracks[:]
	vlc.stdin.write("clear\n")

	source_tracks = []
	for (dirpath, dirnames, filenames) in os.walk(sources_base_dir + sources[cur_source]):
	    source_tracks.extend(filenames)
	    break

	for source_track in source_tracks:
		filename, file_extension = os.path.splitext(source_track)
		if (
			(file_extension == ".wav") or
			(file_extension == ".mp3") or
			(file_extension == ".flac") or
			(file_extension == ".ogg") or
			(file_extension == ".aif") or
			(file_extension == ".aac") or
			(file_extension == ".wma")
		):
			tracks.append(sources_base_dir + sources[cur_source] + "/" + source_track)

		

	tracks.sort()

	for track in tracks:
		vlc.stdin.write("enqueue " + track + "\n")
	
		
	# lcd will be updated automatically using information from the worker thread
	lcd.lcd_string("Src: " + str(cur_source + 1).zfill(2) + "  Trk: --", lcd.LCD_LINE_1)
		
	vlc_if.cur_track = ""
	if bRandom:
		vlc.stdin.write("random on\n")
	else:
		vlc.stdin.write("random off\n")
		

	vlc.stdin.write("play\n")
	time.sleep(1)
	vlc.stdin.write("status\n")

	#wait until playing or timeout
	timeout_counter = 0
	while vlc_if.bStopped:
		timeout_counter += 1
		if timeout_counter > PLAYER_TIMEOUT_COUNT:
			fnc_exit_player()
			break
		
		time.sleep(SLEEP_TIME)  



def fnc_init_player():
	global bPlayerActive
	global cur_source
	global player_update_counter

	lcd.backlight(True)
	fnc_update_alarm_state()
	fnc_update_time(True)

	player_update_counter = 0
	bPlayerActive = True
	fnc_relais(True)

	if cur_source == -1:
		# play default file
		alarm_file = dir_path + "/" + ALARM_FILE
		return

	fnc_open_source()



def fnc_exit_player():
	global bPlayerActive
	global bAlarmActive
	global vlc

	fnc_relais(False)
	vlc.stdin.write("stop\n")
	bPlayerActive = False
	bAlarmActive = False
	fnc_update_time(True)
	fnc_set_mode(MODE_IDX_OFF)



def fnc_next_track():
	vlc.stdin.write("next\n")



def fnc_prev_track():
	vlc.stdin.write("prev\n")



def fnc_show_source():
	global cur_source
	global sources

	items = sources[cur_source].split("/")
	
	if len(items) >= 1:
		lcd.lcd_string(items[0], lcd.LCD_LINE_1)
		time.sleep(LCD_WRITE_TIME_SEC)

	if len(items) >= 2:
		lcd.lcd_string(items[1], lcd.LCD_LINE_2)
	else:
		lcd.lcd_string("                    ", lcd.LCD_LINE_2)

	time.sleep(LCD_WRITE_TIME_SEC)
		
	


def fnc_init_select_source():
	fnc_show_source()



def fnc_select_source():
	global cur_mode
	global bWriteIni

	fnc_open_source()
	bWriteIni = True
	cur_mode = MODE_IDX_PLAYER

	# lcd needs some time
	fnc_update_time(True)
	


def fnc_prev_source():
	global cur_source
	global sources
	global bWriteIni

	cur_source -= 1
	if cur_source < 0:
		cur_source = len(sources) - 1

	fnc_show_source()



def fnc_next_source():
	global cur_source
	global sources
	global bWriteIni

	cur_source += 1
	if cur_source >= len(sources):
		cur_source = 0

	fnc_show_source()





def fnc_read_sources():
	global sources
	global sources_base_dir

	sources_file = dir_path + "/" + SOURCES_FILE
	if os.path.isfile(sources_file):
		f = open(sources_file, "r")
		lines = f.readlines()
		line_idx = 0
		for line in lines:
			line = line.replace("\n", "")
			line = line.replace("\r", "")
			if line_idx == 0:
				# first line contains base directory
				sources_base_dir = line
			elif len(line):
				sources.append(line)

			line_idx += 1
			
		f.close()


	
def fnc_read_settings():
	global sources
	global cur_source
	global bRandom
	global bAlarm
	global alarm_hour
	global alarm_min

	ini_file = dir_path + "/" + INI_FILE
	if os.path.isfile(ini_file):
		f = open(ini_file, "r")
		lines = f.readlines()
		for line in lines:
			line = line.replace("\n", "")
			line = line.replace("\r", "")
			pairs = line.split("=")
			if len(pairs) != 0:
				if pairs[0] == "cur_source":
					cur_source = int(pairs[1])
					if cur_source >= len(sources):
						cur_source = len(sources) - 1
				elif pairs[0] == "random":
					if pairs[1] == "On":
						bRandom = True
					else:
						bRandom = False
				elif pairs[0] == "alarm":
					if pairs[1] == "On":
						bAlarm = True
					else:
						bAlarm = False
				elif pairs[0] == "alarm_hour":
					alarm_hour = int(pairs[1])
				elif pairs[0] == "alarm_min":
					alarm_min = int(pairs[1])
			
		f.close()

	fnc_update_random_state()
	fnc_update_alarm_state()


	
def fnc_write_settings():
	global cur_source
	global bRandom
	global bAlarm
	global alarm_hour
	global alarm_min

	random = "Off"
	if bRandom:
		random = "On"

	alarm = "Off"
	if bAlarm:
		alarm = "On"

	ini_file = dir_path + "/" + INI_FILE
	f = open(ini_file, "w")
	f.write("cur_source=" + str(cur_source) + "\n")
	f.write("random=" + random + "\n")
	f.write("alarm=" + alarm + "\n")
	f.write("alarm_hour=" + str(alarm_hour) + "\n")
	f.write("alarm_min=" + str(alarm_min) + "\n")
		
	f.close()


def fnc_devices(bOn):
	# cut power uptake in half when running (no USB or ethernet except when in exit menu
	if bOn:
		os.system("echo -n 0x1 | sudo tee /sys/devices/platform/soc/20980000.usb/buspower")
		os.system("sudo /etc/init.d/networking start")
	else:
		os.system("sudo /etc/init.d/networking stop")
		os.system("echo -n 0x0 | sudo tee /sys/devices/platform/soc/20980000.usb/buspower")

		

def fnc_init_exit():
	fnc_devices(True)

	lcd.backlight(True)
	lcd.lcd_string("Cncl Exit   POff", lcd.LCD_LINE_2)

	

def fnc_exit_cancel():
	fnc_devices(False)
	fnc_set_mode(MODE_IDX_OFF)



def fnc_release():
	global vlc
	global vlc_if

	vlc_if.bGoDown = True
	vlc.stdin.write("quit\n")
	fnc_relais(False)


	
def fnc_quit():
	fnc_release()

	lcd.lcd_string("Attention!", lcd.LCD_LINE_1)
	lcd.lcd_string("Terminated!", lcd.LCD_LINE_2)
	time.sleep(3)
	lcd.backlight(False)

	exit()
	

# shutdown the system
def fnc_shutdown():
	fnc_release()

	lcd.lcd_string("Attention!", lcd.LCD_LINE_1)
	lcd.lcd_string("Going down!", lcd.LCD_LINE_2)
	time.sleep(3)
	lcd.backlight(False)

	os.system("sudo shutdown now") 



def fnc_go_display():
	fnc_set_mode(MODE_IDX_DISPLAY)	



def fnc_go_player():
	fnc_set_mode(MODE_IDX_PLAYER)



def fnc_go_select_source():
	fnc_set_mode(MODE_IDX_SELECT_SOURCE)



def fnc_go_set_time():
	fnc_get_set_time_date()
	fnc_set_mode(MODE_IDX_SET_TIME_HOUR)


	
def fnc_go_set_alarm():
	fnc_set_mode(MODE_IDX_SET_ALARM_HOUR)



def fnc_go_exit():
	fnc_set_mode(MODE_IDX_EXIT)



# Operating modes table
#

modes = [
	# MODE_IDX_OFF
	[
		"Light Off       ", 
		fnc_init_light_off, 
		[fnc_next_mode, fnc_next_mode, fnc_next_mode], 
		[fnc_none, fnc_none, fnc_none], 
		[fnc_go_exit, fnc_none, fnc_none], 
		[False, False, False],
		MODE_IDX_DISPLAY
	],
	# MODE_IDX_DISPLAY
	[
		"                ", 
		fnc_init_display, 
		[fnc_none, fnc_toggle_random, fnc_toggle_alarm], 
		[fnc_none, fnc_none, fnc_none], 
		[fnc_go_player, fnc_go_set_time, fnc_go_set_alarm], 
		[False, False, False],
		MODE_IDX_OFF
	],
	# MODE_IDX_SET_ALARM_HOUR
	[
		"Set Alarm Hour  ", 
		fnc_init_set_alarm_hour, 
		[fnc_next_mode, fnc_inc_alarm_hour, fnc_dec_alarm_hour], 
		[fnc_none, fnc_inc_alarm_hour, fnc_dec_alarm_hour], 
		[fnc_go_display, fnc_set_fast, fnc_set_fast], 
		[False, True, True],
		MODE_IDX_SET_ALARM_MIN
	],
	# MODE_IDX_SET_ALARM_MIN
	[
		"Set Alarm Minute", 
		fnc_init_set_alarm_min, 
		[fnc_next_mode, fnc_inc_alarm_min, fnc_dec_alarm_min], 
		[fnc_none, fnc_inc_alarm_min, fnc_dec_alarm_min], 
		[fnc_go_display, fnc_set_fast, fnc_set_fast], 
		[False, True, True],
		MODE_IDX_SET_ALARM_HOUR
		
	],
	# MODE_IDX_SET_TIME_HOUR
	[
		"Set Hour        ", 
		fnc_init_set_hour, 
		[fnc_next_mode, fnc_inc_hour, fnc_dec_hour], 
		[fnc_none, fnc_inc_hour, fnc_dec_hour], 
		[fnc_go_display, fnc_set_fast, fnc_set_fast], 
		[False, True, True],
		MODE_IDX_SET_TIME_MIN
	],
	# MODE_IDX_SET_TIME_MIN
	[
		"Set Minute      ", 
		fnc_init_set_min, 
		[fnc_next_mode, fnc_inc_min, fnc_dec_min], 
		[fnc_none, fnc_inc_min, fnc_dec_min], 
		[fnc_go_display, fnc_set_fast, fnc_set_fast], 
		[False, True, True],
		MODE_IDX_SET_DATE_YEAR
	],
	# MODE_IDX_SET_DATE_YEAR
	[
		"Set Year        ", 
		fnc_init_set_year, 
		[fnc_next_mode, fnc_inc_year, fnc_dec_year], 
		[fnc_none, fnc_inc_year, fnc_dec_year], 
		[fnc_go_display, fnc_set_fast, fnc_set_fast], 
		[False, True, True],
		MODE_IDX_SET_DATE_MONTH
	],
	# MODE_IDX_SET_DATE_MONTH
	[
		"Set Month       ", 
		fnc_init_set_month, 
		[fnc_next_mode, fnc_inc_month, fnc_dec_month], 
		[fnc_none, fnc_inc_month, fnc_dec_month], 
		[fnc_go_display, fnc_set_fast, fnc_set_fast], 
		[False, True, True],
		MODE_IDX_SET_DATE_DAY
	],
	# MODE_IDX_SET_DATE_DAY
	[
		"Set Day         ", 
		fnc_init_set_day, 
		[fnc_next_mode, fnc_inc_day, fnc_dec_day], 
		[fnc_none, fnc_inc_day, fnc_dec_day], 
		[fnc_go_display, fnc_set_fast, fnc_set_fast], 
		[False, True, True],
		MODE_IDX_SET_TIME_HOUR
	],
	# MODE_IDX_PLAYER
	[
		"Player          ", 
		fnc_init_player, 
		[fnc_exit_player, fnc_next_track, fnc_prev_track], 
		[fnc_none, fnc_next_track, fnc_prev_track], 
		[fnc_go_select_source, fnc_none, fnc_none], 
		[False, True, True],
		MODE_IDX_OFF
	],
	# MODE_IDX_SELECT_SOURCE
	[
		"Select Source   ", 
		fnc_init_select_source, 
		[fnc_select_source, fnc_next_source, fnc_prev_source], 
		[fnc_none, fnc_next_source, fnc_prev_source], 
		[fnc_none, fnc_none, fnc_none], 
		[True, True, True],
		MODE_IDX_OFF
	],
	# MODE_IDX_EXIT
	[
		"Exit Menu       ", 
		fnc_init_exit, 
		[fnc_none, fnc_none, fnc_exit_cancel], 
		[fnc_none, fnc_none, fnc_none], 
		[fnc_shutdown, fnc_quit, fnc_none], 
		[False, False, True],
		MODE_IDX_OFF
	]

]

# Buttons table
#

buttons = [
	["command", 19, False, False, 0, False, 0], 
	["left", 21, False, False, 0, False, 0], 
	["right", 23, False, False, 0, False, 0]
]


#
# Initialization of hardware
#

lcd = LCDI2C_backpack(0x27)

lcd.lcd_string("Alarm Pi V1.0",lcd.LCD_LINE_1)

rtc = pyRPiRTC.DS1302()
now = rtc.read_datetime()
lcd.lcd_string(str(now),lcd.LCD_LINE_2)


GPIO.setmode(GPIO.BOARD)

for button in buttons:
	GPIO.setup(button[BTN_PIN], GPIO.IN, pull_up_down=GPIO.PUD_UP)
#	print("Setting up pin " + str(button[BTN_PIN]) + " as " + button[BTN_NAME])

GPIO.setup(RELAIS_1_PIN, GPIO.OUT)
GPIO.setup(RELAIS_2_PIN, GPIO.OUT)
fnc_relais(False)

time.sleep(1)

fnc_read_sources()
fnc_read_settings()

fnc_relais(True)

startup_file = dir_path + "/" + STARTUP_FILE
vlc = subprocess.Popen(["vlc", "-I", "oldrc"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
vlc.stdin.write("add " + startup_file + "\n")

vlc_if = vlc_comm()

t = threading.Thread(target=thrd_read_vlc, args=(vlc, True))
t.daemon = True # thread dies with the program
t.start()

time.sleep(6)
lcd.clear()
fnc_relais(False)

fnc_devices(False)
fnc_set_mode(MODE_IDX_DISPLAY)

#
# Main loop
#
button_index = 0
track_index = 0
while 1:
	button_index = 0
	for button in buttons:
		if GPIO.input(button[BTN_PIN]) == 0:
			button[BTN_READ] = True
		else:
			button[BTN_READ] = False

		if button[BTN_STATE] != button[BTN_READ]:
			if not button[BTN_READ]:
				# button is up
				step = 1

				# function is called on button release if not instant action
				if not modes[buttons[button_index][BTN_MODE]][MODE_BTN_INSTANT_ACTION][button_index] and (button[BTN_COUNTER] < REPEAT_PRESS_COUNT):
					modes[buttons[button_index][BTN_MODE]][MODE_BTN_ACTION][button_index]()
			else:
				#button is down
				buttons[button_index][BTN_MODE] = cur_mode
				if modes[buttons[button_index][BTN_MODE]][MODE_BTN_INSTANT_ACTION][button_index]:
					modes[buttons[button_index][BTN_MODE]][MODE_BTN_ACTION][button_index]()

			# set new state
			button[BTN_STATE] = button[BTN_READ]
			# reset state counter
			button[BTN_COUNTER] = 0
			button[BTN_LONG] = False;
			activity_count = 0
		else:
			# increase state counter
			if button[BTN_STATE]:
				activity_count = 0
				button[BTN_COUNTER] += 1
				if button[BTN_COUNTER] >= LONG_PRESS_COUNT and not button[BTN_LONG]:
					modes[buttons[button_index][BTN_MODE]][MODE_BTN_LONG_ACTION][button_index]()
					button[BTN_LONG] = True;
				elif button[BTN_COUNTER] >= REPEAT_PRESS_COUNT:
					modes[buttons[button_index][BTN_MODE]][MODE_BTN_REPEAT_ACTION][button_index]()

		button_index += 1


	if bPlayerActive:
		if vlc_if.bStopped:
			fnc_exit_player()
		elif vlc_if.bNewTrack:
			vlc_if.bNewTrack = False
			track_index = 1
			for track in tracks:
				if track == vlc_if.cur_track:
					lcd.lcd_string("Src: " + str(cur_source + 1).zfill(2) + "  Trk: " + str(track_index).zfill(2), lcd.LCD_LINE_1)
					break
				track_index += 1

		player_update_counter += 1
		if player_update_counter > PLAYER_UPDATE_COUNT:
			# we have to prod vlc constantly to get a status update
			vlc.stdin.write("status\n")
			


	if cur_mode != MODE_IDX_OFF:
		activity_count += 1
		if activity_count >= INACTIVITY_TIMEOUT_COUNT:
			activity_count = 0
			if not bPlayerActive and (cur_mode != MODE_IDX_EXIT):
				fnc_set_mode(MODE_IDX_OFF)

							

	update_count += 1
	if update_count >= UPDATE_TIME_COUNT:
		update_count = 0
		fnc_update_time()
		if bAlarm and not bAlarmActive:
			if (time_hour == alarm_hour) and (time_min == alarm_min):
				bAlarmActive = True
				fnc_go_player()
		

	# scan buttons every 100 milliseconds
	time.sleep(SLEEP_TIME)  
 
