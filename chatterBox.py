#!/usr/bin/env python
# -*- coding: utf-8 -*-
#handysnipz
#      z = self.builder.get_object('label1')
#      print 'button1.label:',z.get_text()
#      z.set_text('anderweise')


import sys, socket, time, glib
try:  
    import pygtk  
    pygtk.require("2.0")  
except:  
    pass  
try:  
    import gtk  
except:  
    print("GTK Not Availible")
    sys.exit(1)
import pygst
pygst.require("0.10")
import gst
# -------------------------------------------

class chatter: 
# prototypes for Alice and Bob objects 
  localIP = '127.0.0.1'
  localPort = 9000
  remoteIP = '0.0.0.0'
  remotePort = ''

class thing1:

  def __init__(self):
#---- vars to make at instantiation	  
    tox = 0
    allow_polling = False

#---- build interface (using gtk.Builder)  
    self.builder = gtk.Builder()
    self.builder.add_from_file("chatterBox.glade")
    dic = {"on_window1_destroy" : self.quit,
           "mouseEnter" : self.mouseEnter,
           "mouseExit" : self.mouseExit,
           "onLocalPortChanged" : self.onLocalPortChanged}
    self.builder.connect_signals( dic )

# ----------------------------------
# Create the gstreamer pipelines
# (to be configged before actually using, though)
# (config will set IPaddys and Ports, and probably caps as well)

# desired pipeline is as follows:
# gst-launch-0.10 tcpserversrc host=192.168.1.142 port=5000 ! decodebin ! xvimagesink
# where host and port point to IP and port of Alice
# and xvimagesink gets stuffed into the gtkDrawingArea (later)

# ---- playerIn pipeline ----------------------
    self.playerIn = gst.Pipeline("playerIn")
    self.sourceIn = gst.element_factory_make("tcpserversrc", "sourceIn")
    self.dcb = gst.element_factory_make("decodebin", "dcb")
    self.dcb.connect("new-decoded-pad", self.new_decode_pad)
    self.sinkIn = gst.element_factory_make("xvimagesink", "sinkIn")

    self.playerIn.add(self.sourceIn, self.dcb, self.sinkIn)
    gst.element_link_many(self.sourceIn, self.dcb)

    self.busIn = self.playerIn.get_bus()
    self.busIn.add_signal_watch()
    self.busIn.connect("message", self.busIn_on_message)
# busIn will need to have synch messaging enabled in order to make 
# xvimagesink (aka sinkIn) fit into the GUI's drawingarea
#self.fingers.cross()
    self.busIn.enable_sync_message_emission()
    self.busIn.connect("message", self.busIn_on_message)
    self.busIn.connect("sync-message::element", self.on_sync_message)


# ---- playerOut pipeline -----------------------

#gst-launch-0.10 v4l2src ! video/x-raw-yuv,width=320,height=240 ! theoraenc ! oggmux ! tcpclientsink host=127.0.0.1 port = 9000
    self.playerOut = gst.Pipeline("playerOut")
    self.sourceOut = gst.element_factory_make("v4l2src", "camsrc")
    self.caps = gst.Caps("video/x-raw-yuv,width=320,height=240")
      #^^ subject to later change^^

    self.filterOut = gst.element_factory_make("capsfilter", "filter")
    self.filterOut.set_property("caps", self.caps)
      #^^ note: assuming this is dynamic,and that changing caps    ^^
      #^^ properties later will propogate -- check this assumption ^^

    self.theoEnc = gst.element_factory_make("theoraenc", "theoenc")
    self.oggmuxer = gst.element_factory_make("oggmux", "oggmuxer")

    self.sinkOut = gst.element_factory_make("tcpclientsink", "sinkOut")
      # this should be a UDP port, but... patience grasshopper

    self.conv = gst.element_factory_make ("ffmpegcolorspace", "conv")
    self.playerOut.add(self.sourceOut, self.filterOut, self.theoEnc, 
                       self.oggmuxer, self.sinkOut)
    gst.element_link_many(self.sourceOut, self.filterOut, 
                          self.theoEnc, self.oggmuxer, self.sinkOut)

    self.busOut = self.playerOut.get_bus()
    self.busOut.add_signal_watch()
    self.busOut.connect("message", self.busOut_on_message)
#-----------------------------------
############## stop  OUT snippy  ##########################
#(don't delete below yet, need to "steal" synch-messaging))
# also found in 'snappy's

# (replace this with the nicer version)
# see: configurePipeOutbound() 
# and  configurePipeInbound() 
#    self.player = gst.parse_launch ("audiotestsrc ! alsasink")
#    self.player = gst.parse_launch ("v4l2src ! video/x-raw-yuv,width=320,height=240 ! ffmpegcolorspace ! theoraenc ! oggmux ! tcpclientsink host=192.168.1.101 port=3000" )
#    ! alsasink")
#    bus = self.player.get_bus()
#    bus.add_signal_watch()
#    bus.enable_sync_message_emission()
#    bus.connect("message", self.on_message)
#    bus.connect("sync-message::element", self.on_sync_message)

#    self.player2 = gst.parse_launch ("audiotestsrc freq = 600 ! alsasink")
#    bus2 = self.player2.get_bus()
#    bus2.add_signal_watch()
#    bus2.enable_sync_message_emission()
#    bus2.connect("message", self.on_message)
#    bus2.connect("sync-message::element", self.on_sync_message)
    print 'made pipelines'
# ----------------------------------
    
    
    
# ------get IP addys, set in GUI --------  
    z = self.builder.get_object('label10')
    try:
        Alice.localIP = self.getLocalIP()
#        print 'Alice\'s local is: ', Alice.localIP
        z.set_text(Alice.localIP)
    except socket.gaierror:
        Alice.localIP = '127.0.0.1'
        print 'unable to connect'
        print 'Alice.localIP = ', Alice.localIP
        z.set_text(Alice.localIP)
        y = self.builder.get_object('entry6') # statusbar text object
        y.set_text('Please make sure you are connected to the internet')

    print 'Alice\'s local is: ', Alice.localIP
    print 'Bob\'s local is: ', Bob.localIP
#--end __init__ ---------------------------------
  def configurePipeInbound(self):
	  # -- changed to only set, not create
#      self.sourceIn.set_property("host", '127.0.0.1' )
      self.sourceIn.set_property("host", Alice.localIP )
#      self.sourceIn.set_property("host", '192.168.1.142' )
      #this should be "Alice's" IP address

      self.sourceIn.set_property("port", 9000 )
      #this should be "Bob's" listening port
#-----------------------------------
  def configurePipeOutbound(self):
# changed to only set, not create
#gst-launch-0.10 v4l2src ! video/x-raw-yuv,width=320,height=240 ! theoraenc ! oggmux ! tcpclientsink host=127.0.0.1 port = 9000

# should probably do caps setting here, rather than in __init__, but... 
# it needs to be in __init__ too, it seems.

#      self.sinkOut.set_property("host", '127.0.0.1' ) 
      self.sinkOut.set_property("host", Bob.localIP)
#      self.sinkOut.set_property("host", '192.168.1.101') 
      #this should be "Bob's" IP address
      self.sinkOut.set_property("port", 9000 )
      #this should be "Bob's" listening port
#-----------------------------------
  def getLocalIP(self):
      s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      s.connect(("google.com",80))
      addy = s.getsockname()[0]

#      try:
#          s.connect(("google.com",80))
#          addy = s.getsockname()[0]
#      except socket.gaierror:
#          addy = 'connectFailed'         
      return addy
#-----------------------------------      
  def mouseEnter(self, widget):
      print 'setting gst.STATE_PLAYING'
      print 'configging INpipe'
      self.configurePipeInbound()
      self.playerIn.set_state(gst.STATE_PLAYING)
      time.sleep(1)

      print 'configging outpipe'
      self.configurePipeOutbound()
      self.playerOut.set_state(gst.STATE_PLAYING)

#-----------------------------------
  def mouseExit(self, widget):
# don' you do nuthin', punk!
    pass
#      print 'setting gst.STATE_NULL'
#      self.playerIn.set_state(gst.STATE_NULL)
#-----------------------------------
  def mouseEnter2(self, widget, data): #bakk
      print 'mouseEntered'
      print 'self:', self
      print 'widget:', widget
      print 'data:', data
      z = self.builder.get_object('label1')
      print 'button1.label:',z.get_text()
      z.set_text('anderweise')
      self.ticktock()
      print '-------'
#------------------------------------
  def busIn_on_message(self, bus, message):
      t = message.type
      if t == gst.MESSAGE_EOS:
          self.playerIn.set_state(gst.STATE_NULL)
#          self.button.set_label("Start")
      elif t == gst.MESSAGE_ERROR:
          err, debug = message.parse_error()
          print "Error: %s" % err, debug
          self.playerIn.set_state(gst.STATE_NULL)
#          self.button.set_label("Start")
#------------------------------------
  def busOut_on_message(self, bus, message):
      t = message.type
      if t == gst.MESSAGE_EOS:
          self.playerOut.set_state(gst.STATE_NULL)
#          self.button.set_label("Start")
      elif t == gst.MESSAGE_ERROR:
          err, debug = message.parse_error()
          print "Error: %s" % err, debug
          self.playerOut.set_state(gst.STATE_NULL)
#          self.button.set_label("Start")
#-----------------------------------
  def onLocalPortChanged(self, widget, data):
      print 'local port changed'
      print 'wgt', widget.get_text()
      if self.playerIn.get_state() == gst.STATE_NULL:
		  # TODO - should really use a callInProgress boolean
          Alice.localPort = widget.get_text()
          print "Alice.localPort now = ", Alice.localPort
          #--set Alice's local port to entry text
      else:
          print 'Don\t change port while stream active'
          #set text back to Alice's port
#-----------------------------------
  def new_decode_pad(self, dbin, pad, islast):
      dec_pad = self.sinkIn.get_pad("sink")
      pad.link(dec_pad)
#-----------------------------------
  def on_sync_message(self, bus, message):
      print 'got SyncMssg'
      if message.structure is None:
          return
      message_name = message.structure.get_name()
      print 'onSyncMssgName = ',message_name
      if message_name == "prepare-xwindow-id":
          # Assign the viewport
          imagesink = message.src
          print "message.src = ", imagesink
          imagesink.set_property("force-aspect-ratio", True)
          z = self.builder.get_object('drawingarea1')
          imagesink.set_xwindow_id(z.window.xid)
          #but it ain't no "self.movie_window" - plug right critter in here
#-------------------------------------
  def startPolling(self, widget):
      if self.allow_polling == False:
          self.allow_polling = True
          glib.timeout_add(2000, self.ticktock)
          z = widget.get_name()
          print 'widgetname=',z
      return
#-----------------------------------
  def stopPolling(self, widget):
      self.allow_polling = False
      z = self.builder.get_object('button1')
      zz = z.get_name()
      print 'widgetnamez=',z.name
      print 'widgetnamezz=',zz
      return
#-----------------------------------
  def ticktock(self):
      if self.allow_polling:
          self.tox += 1
          print 'tix:', self.tox
          return True
      else:
          return False
#-----------------------------------
  def quit(self, widget):
      self.playerOut.set_state(gst.STATE_NULL)
      print "playerOutState = NULL"
      self.playerIn.set_state(gst.STATE_NULL)
      print "playerINState = NULL"
      
      sys.exit(0)

Alice = chatter()  #local participant
Bob = chatter()    # remote participant
Bob.localIP = '192.168.1.101'
thing1 = thing1()
gtk.main()
