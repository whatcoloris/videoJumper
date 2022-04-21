import cv2, numpy as np
#import sys
import sys, os, pyaudio, random
from pocketsphinx.pocketsphinx import *
from sphinxbase.sphinxbase import *
from time import sleep
import time

modeldir = "/usr/share/pocketsphinx/model"

start = time.time()

# Create a decoder with certain model
config = Decoder.default_config()
config.set_string('-hmm', os.path.join(modeldir, 'en-us/en-us'))
#config.set_string('-dict', os.path.join(modeldir, 'en-us/cmudict-en-us.dict'))
config.set_string('-allphone', os.path.join(modeldir, 'en-us/en-us-phone.lm.bin'))
#config.set_string('-keyphrase', 'forward')
config.set_float('-kws_threshold', 1e+20)
config.set_string('-verbose', 'False')
config.set_string('-no_search', 'False')
config.set_string('-full_utt', 'False')

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
stream.start_stream()

def flick(x):
    pass

cv2.namedWindow('image')
#cv2.moveWindow('image',250,150)
cv2.setWindowProperty('image', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
#cv2.namedWindow('controls')
#cv2.moveWindow('controls',250,50)

#controls = np.zeros((50,750),np.uint8)
#cv2.putText(controls, "W/w: Play, S/s: Stay, A/a: Prev, D/d: Next, E/e: Fast, Q/q: Slow, Esc: Exit", (40,20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 255)

video = sys.argv[1] 
cap = cv2.VideoCapture(video)

tots = cap.get(cv2.CAP_PROP_FRAME_COUNT)
i = 0
cv2.createTrackbar('S','image', 0,int(tots)-1, flick)
cv2.setTrackbarPos('S','image',random.randrange(int(tots)-1))

cv2.createTrackbar('F','image', 1, 100, flick)
frame_rate = 30
cv2.setTrackbarPos('F','image',frame_rate)

def process(im):
    return cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

status = 'stay'



# Process audio chunk by chunk. On keyphrase detected perform action and restart search
decoder = Decoder(config)
decoder.start_utt()

framejump = 3
invertit = False

while True:
  elapsed = time.time() - start
  #cv2.imshow("controls",controls)
  try:
    buf = stream.read(1024)
    if i==tots-1:
      i=0
    cap.set(cv2.CAP_PROP_POS_FRAMES, i)
    ret, im = cap.read()
    size = 1920.0

    r = size / im.shape[1]
    dim = (int(size), int(im.shape[0] * r))
    im = cv2.resize(im, dim, interpolation = cv2.INTER_AREA)
    #these lines just for testing, so we can "escape" if need be
    #if im.shape[0]>600:
        #im = cv2.resize(im, (500,500))
        #controls = cv2.resize(controls, (im.shape[1],25))
    #cv2.putText(im, status, )
    inversion = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    if (invertit):
        cv2.imshow('image', inversion)
    else:
        cv2.imshow('image', im)
    status = { ord('s'):'stay', ord('S'):'stay',
                ord('w'):'play', ord('W'):'play',
                ord('r'):'playreverse', ord('W'):'playreverse',
                ord('a'):'prev_frame', ord('A'):'prev_frame',
                ord('d'):'next_frame', ord('D'):'next_frame',
                ord('q'):'slow', ord('Q'):'slow',
                ord('e'):'fast', ord('E'):'fast',
                ord('c'):'snap', ord('C'):'snap',
                -1: status, 
                27: 'exit'}[cv2.waitKey(10)]
    if buf:
         decoder.process_raw(buf, False, False)
    else:
         break
    if decoder.hyp() != None:
        hypothesis = decoder.hyp()
        teststr = hypothesis.hypstr
        if ("V" in teststr):
            print("jump")
            randomplacetojump = random.randrange(int(tots)-1)
            cv2.setTrackbarPos('S','image',randomplacetojump)
            i = cv2.getTrackbarPos('S','image')
            status = "play"
        if ("AA" in teststr):
            print("speed up")
            frame_rate = min(100,frame_rate+framejump)
            cv2.setTrackbarPos('F', 'image', frame_rate)
            status = "play"
        if ("R" in teststr):
            print("slow down")
            frame_rate = max(frame_rate-framejump, 0)
            cv2.setTrackbarPos('F', 'image', frame_rate)
            status = "play"
        if ("IY" in teststr):
            print("reverse")
            status = "playreverse"
        #if ("S\r" or "S\n" in teststr):
            #print("inversion")
            #invertit = False
        if ("P" in teststr):
            print("inversion")
            invertit = True
        #if ("IY" in teststr):
        #    print("reverse")
        #    status = "playreverse"
        if ("D" in teststr):
            print("noninversion")
            invertit = False
        decoder.end_utt()
        decoder.start_utt()
    if status == 'play':
      frame_rate = cv2.getTrackbarPos('F','image')
      sleep((0.1-frame_rate/1000.0)**21021)
      i+=1
      cv2.setTrackbarPos('S','image',i)
      continue
    if status == 'playreverse':
      frame_rate = cv2.getTrackbarPos('F','image')
      sleep((0.1-frame_rate/1000.0)**21021)
      i-=1
      cv2.setTrackbarPos('S','image',i)
      continue
    if status == 'stay':
      i = cv2.getTrackbarPos('S','image')
    if status == 'exit':
        break
    if status=='prev_frame':
        i-=1
        cv2.setTrackbarPos('S','image',i)
        status='stay'
    if status=='next_frame':
        i+=1
        cv2.setTrackbarPos('S','image',i)
        status='stay'
    if status=='slow':
        frame_rate = max(frame_rate - 5, 0)
        cv2.setTrackbarPos('F', 'image', frame_rate)
        status='play'
    if status=='fast':
        frame_rate = min(100,frame_rate+5)
        cv2.setTrackbarPos('F', 'image', frame_rate)
        status='play'
  except KeyError:
      print("Invalid Key was pressed")
cv2.destroyWindow('image')
