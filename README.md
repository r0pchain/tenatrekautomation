

# TenaControls Trek Board Automations

Flask-based application to automate TenaControls' model lighting boards


## Overview
TenaControls makes some really cool lighting boards for scaled science-fiction models, but they require you to use a fiddly proprietary app to control them

I figured out how to communicate over Bluetooth with my own Trek-model Tena board by snooping Bluetooth and set up this automation on a Pi Zero 2 W so I can control it with Home Assistant and voice assistants in my home.  

I've also written a [replacement Android open source app](https://github.com/r0pchain/tenatrekboard) to ensure these TenaControls boards continue to work with modern Android phones.

## CONOP
Depending on the level of automation you want to do with your TenaControls model lighting board, you may not need to do all of this. I rely on automations and voice assistants in my home **heavily** - some of my light switches only exist virtually! - so you may not need all this, but as my use case is "comprehensive", it should cover yours as well.

**We will**

 - Use a Raspberry Pi Zero 2 W running raspbian, and then
 - apt-get the bluez, python3-bluez and bluez-tools packages, so we can
 - Pair the TenaControls lighting board with the Pi using bluetoothctl, and then
 - apt-get python3-flask, so we can
 - Create a Flask app, and then
 - Add that Flask app to the systemctl daemon service so it will launch on startup, and then
 - Expose the Flask app to the internet using ngrok, Cloudflare Tunnels etc, so we can
 - Create an IFTTT/SharpTools webhook automation, and then
 - Create a virtual switch in SmartThings or Home Assistant, so we can
 - Connect the virtual switch to IFTTT automation to send a webhook when triggered, and then
 - Have our voice assistant detect the virtual switch, so we can
 - Create a voice assistant routine that will trigger the virtual switch, turning everything on!

## The Flask App
The Flask app included in this project is the "brains" of our automation, and essentially serves as a translation layer between web requests and the Bluetooth serial communication commands that the TenaControls board expects. The serial commands for the board are embedded into the app.py script which listens on port 1701 for the command dictionary below. I placed it in **/home/pi/flask_bluetooth** and then tested it with **python3 /home/pi/flask_bluetooth/app.py** and sent a few commands using cURL to ensure my TenaControls board was receiving the serial commands OK. **Make sure you change the MAC to match the one you paired earlier!**

Those cURL commands looked something like:
**curl -X POST http://192.168.1.10:1701/send -H "Content-Type: application/json" -d '{"command": "saucer"}'**

The Flask app also includes a simple web page it runs along with it that allows you to press buttons on an HTML page and interact with the hobby board; note that this is important as the TenaControls board seems to only support one serial connection to it at a time, meaning if you're expecting to use this for automation all the time, you'll never really be able to use the TenaControls app ever again and will need to use this button page instead.

Once I was satisfied this was working, I needed to make sure this app would start on boot.

## Persisting the Flask App Across Reboots

All of this is not really useful if the RPi can't go up/down at will and return to a functional state without any intervention. 

First **nano /etc/systemd/system/bluetooth-rfcomm.service** making sure to replace the MAC address with the one you paired with. 
    
    [Unit]
    Description=Bluetooth RFCOMM binding for TenaControls board
    After=bluetooth.target
    
    [Service]
    ExecStart=/bin/bash -c 'rfcomm bind 0 98:98:98:98:98:98 3'
    ExecStop=/bin/bash -c 'rfcomm release 0'
    Restart=always
    User=root
    
    [Install]
    WantedBy=multi-user.target



And then **nano /etc/systemd/system/flask-bluetooth.service**

    [Unit]
    Description=Flask Bluetooth Control Server
    After=network.target bluetooth-rfcomm.service
    
    [Service]
    User=pi
    WorkingDirectory=/home/pi/flask_bluetooth
    ExecStart=/usr/bin/python3 /home/pi/flask_bluetooth/app.py
    Restart=always
    
    [Install]
    WantedBy=multi-user.target

Then
**systemctl daemon-reload
systemctl enable flask-bluetooth.service
systemctl start flask-bluetooth.service
systemctl status flask-bluetooth.service**

And you should Flask running and listening for connections on port 1701. 

## Accessing the Flask App Remotely
You need to set up ngrok or some other way for internet-webhooks to send commands to this Flask app. You could theoretically open a port on your router and go through that, but I don't really recommend it. For something as lightweight and non-production as this, my go-to is Cloudflare Tunnels, which I use extensively for command and control of home automation as it is way more secure than opening a port to the internet. I set my Cloudflare tunnel up to point a hostname into my rPi on my internal network on http://192.168.1.10:1701. At this point, I like to again use cURL to verify the tunnel is working before proceeding, but replace your internal rPI IP address with the external domain name. 

## SmartThings Setup
Modern SmartThings includes a device driver to set up virtual switches. Their app and GUI are incomplete at best, and I find this task is easier to use the SmartThings CLI for.

    smartthings virtualdevices:create-standard --local
    
    ? Device Name: TENA-TRIGGER-LIGHTS
    ─────────────────────────────────────────
     #  Name           Id
    ─────────────────────────────────────────
     1  Switch         VIRTUAL_SWITCH
     2  Dimmer Switch  VIRTUAL_DIMMER_SWITCH
    ─────────────────────────────────────────
    ? Select a device prototype. 1
    Main Info
    ─────────────────────────────────────────────────────────
     Label              TENA-TRIGGER-LIGHTS
     Name               TENA-TRIGGER-LIGHTS
     Id                 <ID appears here>
     Type               VIRTUAL
     Manufacturer Code
     Location Id        <ID appears here>
     Room Id            <ID appears here>
     Profile Id         <ID appears here>
     Capabilities       switch
     Child Devices
    ─────────────────────────────────────────────────────────
    
    
    Device Integration Info (from virtual)
    ─────────────────────────────────────────────────
     Name       TENA-TRIGGER-LIGHTS
     Hub Id     <ID appears here>
     Driver Id  <ID appears here>
    ─────────────────────────────────────────────────
Now you have a virtual switch in your SmartThings instance which will allow you to create home automations as well as proxy this device into a voice assistant for additional automation. I also recommend at this point you set up a local routine to turn this switch off 10 seconds after it turns on; as all of our future automation will be based on the "on" event of this switch, it will just make things run more smoothly. 

## The Automation Webhook
There are a lot of automation listeners out there that allow you to receive an event and then trigger a webhook; my favorite is If This Then That (IFTTT) as it also integrates nicely with SmartThings. You can also go direct with Home Assistant to trigger these, but I find HA a bit annoying to use (constant need to restart HA for changes, "tinker-tier" support vs being closer to "home-prod etc) so I stick with IFTTT. 

My high-level workflow for IFTTT was:
#### **Create an IFTTT Applet**
1.  Click **"If This"** → Search **SmartThings**.
2.  Choose **"Switch turns on"** 
3.  Select your **virtual switch** (created earlier).
4.  Click **"Then That"** → Search **Webhooks**.
5.  Choose **"Make a web request"**.

#### **Configure the Web Request**

-   **URL:**
    
    `http://cloudflaretunnel.hostname/send` 
    
    (Point this to your cloudflare tunnel hostname configured earlier)
    
-   **Method:** `POST`
    
-   **Content Type:** `application/json`
    
-   **Body:**
    
    `{ "command": "demo" }` 
    

✅ **Click "Create Action"** and **Enable the Applet**.

## The Voice Assistant
Assuming you already have your SmartThings connected to Alexa or Google Home etc, you should now be able to see that virtual switch in there and interact with it; clicking it should result in the webhook you configured in IFTTT to hit your Flask application. Create a new routine in your voice assistant that will turn on this virtual switch whenever you give some witty command like "engage", thus cementing your tech sophistication and nerd cred with all three of your friends. 


## Command Dictionary
    "saucer": lights up the saucer lighting on the primary hull
    "secondary": on my board, lights up the display base
    "neck": lights up auxillary external lights for the model
    "chiller": chiller grill lighting on nacelles
    "nav": navigation lights
    "strobe": strobe blinkies
    "impulse": impulse thrusters
    "deflector": deflector dish
    "photon": fire photon torpedoes
    "phaser": fire phasers
    "warp": warp mode - per how the original TenaControls app works, you press this and then "delfector" to engage mode
    "play1": plays a pre-recorded sound clip, if eqipped on your board
    "play2": plays a pre-recorded sound clip, if eqipped on your board
    "play3": plays a pre-recorded sound clip, if eqipped on your board
    "play4": plays a pre-recorded sound clip, if eqipped on your board
    "play5": plays a pre-recorded sound clip, if eqipped on your board
    "play6": plays a pre-recorded sound clip, if eqipped on your board
    "play7": plays a pre-recorded sound clip, if eqipped on your board
    "play8": plays a pre-recorded sound clip, if eqipped on your board
    "play9": plays a pre-recorded sound clip, if eqipped on your board
    "play10": plays a pre-recorded sound clip, if eqipped on your board


## Parting Thoughts
This is a project I envisioned back in 2019 when I first got my Enterprise 1701-A 1/350 model set up. I'm sure I could have done it then, but the technologies introduced in the intervening six years have made this much easier, much cheaper, and much more secure than it would have been then; what initially started me down this road was [needing to build a modern Android app because TenaControls won't update theirs and it won't run without you forcing it down with adb in modern Android kernels.](https://github.com/r0pchain/tenatrekboard/blob/master/README.md#the-tech-details) I guess I'm happy that's the impetus for finally making this happen, but wish that more hobby board manufacturers would just open source so people like me wouldn't have to hack this together. 



