# schellenberg-mqtt
Daemon which allows to send commands to rollershutters from Schellenberg through MQTT


## MQTT Commands

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
