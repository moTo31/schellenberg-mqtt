# schellenberg-mqtt
Linux Daemon which allows to send commands to rollershutters from Schellenberg through MQTT. Most of the MQTT related part was taken from [The miflora MQTT daemon from ThomDietrich](https://github.com/ThomDietrich/miflora-mqtt-daemon). Furthemore I used information from [LoPablos reverse engineering of the schellenberg USB](https://github.com/LoPablo/schellenberg-qivicon-usb). Thank you all for your effort!

## Requirements
For this daemon to work properly you need:
- The original Schellenberg USB device inserted in a USB port e.g. of your Raspberry Pi.
- A working MQTT broker this daemon will connect to
- A Schellenberg rollershutter that accepts commands from the Schellenberg USB
   - Additionally, the rollershutter must have been paired to the USB before (instructions see below)


## Configuration

### Pairing a rollershutter with the Schellenberg USB

I used a Schellenberg Rollodrive 75 Premium for pairing, I hope it works the same way for other devices, if not please let me know and I will add it here.

I tried to write a step by step guide to pair one rollershutter with the USB:
1.  Plug in your Schellenberg USB
2.  Open a console and enter `dmesg | grep tty`
    1.  This should provide the device id the command shall be sent to (in my case this was `ttyACM0`)
3.  Define a one byte hex code for your device (e.g. `C4`, this must be used in the pairing command in step 5)
    1.  There seems to be an allowed range for these device ids (e.g. `00` and `01` was not working for me). So just use something in the middle between `00` and `FF`..
4.  Activate the program mode of your roller shutter (according the manual of your rollershutter)
5.  Within 10 seconds (!) after the activation of the program mode, you must send the pairing command to your device by using 'echo'.
    1.  The structure of the command looks as follows: `ssXX9600000`  where XX is the one byte id you selected for your device (e.g. `C4`)
    2.  So, an example command with the device id `C4` would be `echo 'ssC49600000' > /dev/ttyACM0` (if your device is `ttyACM0`, otherwise replace accordingly)
6.  The successful pairing should end the program mode of the rollershutter and you should be able to send commands now
7.  Test the pairing by sending e.g. a down command to your roller shutter 
    1.  `echo 'ssC49010000' > /dev/ttyACM0` (still, I am using `C4` as device ID so replace it with your selected one)
8.  If it works, congratulations! If it doesnt, repeat the pairing with a different device ID or check again you really activated the program mode of your rollershutter

Hint: If you want to see the answers of the USB device when sending commands, you can use [tio](https://github.com/tio/tio). To listen to commands just start a second shell and enter `tio -b 9600 /dev/ttyACM0`

### Setting up the daemon

**Important**: The rollershutter must have been paired with the Schellenberg USB stick before any commands can be sent to it, this needs to be done manually and is explained in the chapter above.
The `deviceEnumerator` is the one byte hex device id used during the pairing process.

As I described in the requirements, you need to have an MQTT broker ready where this daemon will connect to.
Check the `config.ini` and adapt the parameters accordingly.

In order to send a command, you just send a json string to the basetopic. This json currently does only support two mandatory parameters:
- `deviceEnumerator`
  - Device id you want to control (one byte hex), this device must have been paired with the USB first!
  - Example: `"deviceEnumerator" : "C4"`
- `command`
  - Command you want to send. The list of allowed commands is shown below
  - Example: `"command" : "down"`

#### Supported Commands
| Command Name    | Explanation                         |
| --------------- | ----------------------------------- |
| stop            | Stops movement of the rollershutter |
| up              | Move Rollershutters Up              |
| down            | Move Rollershutters Down∏           |
| windowHandle0   | Window Handle Position 0°           |
| windowHandle90  | Window Handle Position 90°          |
| windowHandle180 | Window Handle Position 180°         |

#### Example Json

```json
{
    "deviceEnumerator" : "C4",
    "command" : "down"
}
```

## Run

Make sure all configurations and the MQTT broker are setup, before running the daemon. 

### Single Use
`python3 schellenberg-mqtt-daemon.py`

### Continuous Daemon/Service
Assuming you cloned the repository to `/opt/`, otherwise you need to change all paths accordingly

```
sudo cp /opt/schellenberg-mqtt/template.service /etc/systemd/system/schellenberg.service

sudo systemctl daemon-reload

sudo chmod 666 /dev/ttyACM0  

sudo systemctl start schellenberg.service
sudo systemctl status schellenberg.service

sudo systemctl enable schellenberg.service
```