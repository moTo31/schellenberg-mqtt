# schellenberg-mqtt
Daemon which allows to send commands to rollershutters from Schellenberg through MQTT


## Configuration

For now, only json commands with two mandatory parameters are allowed:

**Important**: The rollershutter must have been paired with the Schellenberg USB stick before any commands can be sent to it, this needs to be done manually.
The `deviceEnumerator` is the one byte hex device id used during the pairing process.
Currently, the following commands are supported:

### Supported Commands
| Command Name    | Explanation                         |
| --------------- | ----------------------------------- |
| stop            | Stops movement of the rollershutter |
| up              | Move Rollershutters Up              |
| down            | Move Rollershutters Down∏           |
| windowHandle0   | Window Handle Position 0°           |
| windowHandle90  | Window Handle Position 90°          |
| windowHandle180 | Window Handle Position 180°         |

### Example

```json
{
    "deviceEnumerator" : "C4",
    "command" : "down"
}
```
## Setup

### Single Use
`python 3 python3 schellenberg-mqtt-daemon.py`

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