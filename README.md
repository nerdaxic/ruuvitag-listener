# RuuviTag Sensor Listener for Home Assistant #
## Add [RuuviTag](https://ruuvi.com/ruuvitag/) Enviromental Sensors to Home Assistant


## What the project does ##
My implementation using [ruuvitag_sensor](https://pypi.org/project/ruuvitag-sensor/) library to write measurements from RuuviTags into a .json file, for Home Assistant to read them as a [file sensor](https://www.home-assistant.io/integrations/file/#sensor) every few minutes.

1. Listens for RuuviTags around with whitelisted MAC-addresses.
2. Writes the measurements down in a .json file.
3. The Home Assistant reads the file, and handles it as sensor data.
4. If the sensor is out of range, or out of battery, previous known value will be used. No false-zero readings in Home Assistant.

![RuuviTag](https://pbs.twimg.com/media/E3l5l_BXIAEskmq?format=jpg&name=large)

## Why the project is useful ##

Provided as a sample code for others, to learn how the library can be used. Code should be working and used as is to connect RuuviTags to Home Assistant.
Tested on Rapsberry Pi 4 8GB and Python 2.7.16.

- Automatic configuration.yaml generation, so you don't have to type a lot of complicated config lines.
- Automatic customize.yaml generation, for icons & sensor classes for the RuuviTags.

## How users can get started with the project ##

### 1. Files should be installed to:
**/custom-components/ruuvitag-listener** folder in your home assistant config directory.
For example:
```
/home/pi/docker/hass/custom_components/ruuvitag-listener/measure.py
```
**Descriptions:**

|File|Description|
|----|-----|
|measure.py|Does the measuring and config file generation. Run this with crontab (without parameters)!|
|sensor_list.json|List of your RuuviTags, used to ignore neighbour's sensors and generating the configs.|
|sensor_list.sample.json|Sample of sensor list. Add your tags and remove the ".sample" from filename.|
|configuration.txt¹|Contains rows to be added to configuration.yaml. Tells Home Assistant how to read the sensor file.|
|customization.txt¹|Contains rows to be added to customize.yaml. Sensor icons, device classes etc.|
|.gitignore|Lists the files containing identifiable information, please don't push these into GIT.|

_¹Created in step 6._

### 2. Install _ruuvitag-sensor_ library
Library does all the heavy lifting with bluetooth handling and whatnot.
```bash
pip install ruuvitag_sensor
```

### 3. Install BlueZ 
Needed by _ruuvitag-sensor_ library to access the hardware.
```bash
sudo apt-get install bluez bluez-hcidump
```

### 4. Add your sensors to the sensor_list.json file like so:
Rename **sensor_list.sample.json** file to **sensor_list.json** and add your tags names and MAC-adresses.

I recommend to use simple, single-word english names for the config file generation to work and easier management. You can rename these in Home Assistant customizer to your native language.

You can find your MAC-addresses using RuuviStation mobile app or using _ruuvitag-sensor_ library [sample code](https://pypi.org/project/ruuvitag-sensor/). 
```json
{"D5:3A:AA:CC:8E:4F": "Sauna",
 "D2:43:BC:EE:60:88": "Bedroom",
 "ED:80:DE:71:AC:B4": "Balcony",}
```

### 5. Refresh data automatically with cron
Add line to crontab to refresh data every 5 minutes. This is done outside the Home Assistant's docker container, container just has access to the resulting measurements.json file. Should work fine with the default "pi" user.
**Edit crontab:**
```bash
crontab -e
```
**Add line:**
```bash
*/5 * * * *  python /home/pi/docker/hass/custom_components/ruuvitag-listener/measure.py
```

### 6. Generate the config for Home Assistant:
Each RuuviTag you have will show up as 4 sensors in Home Assistant. Adding these manually is a piece of turd work so this will generate the configs for you automatically.
- Temperature [°C]
- Humidity [% (RH)]
- Air pressure [hPa]
- RuuviTag's battery [V]
- (Optional) Average temperature from multiple sensors [°C]
- (Optional) Absolute humidity [g/m³]

**Generate config files**
```bash
python /home/pi/docker/hass/custom_components/ruuvitag-listener/measure.py --config
```

#### Additional flags:
**Add absolute humidity** sensors to config file. These are calculated from relative humidity and temperature.
```bash
measure.py --config --absolute
```
**Add average temperature and humidity** sensors to config file. Maybe not useful on it's own, but after manual edit can be used for things like "Average indoor temperature" by averaging multiple room's sensor data into one virtual thermometer.

```bash
measure.py --config --average
```

### 7. Copy the sensor configs
Copy the generated configurations to Home Assistant's config files.

```txt
configuration.txt --> configuration.yaml
customization.txt --> customize.yaml
```

You might need to add the customize.yaml into the configuration.yaml file, and possibly to whitelist the custom-component folder (which I doubt):
```yaml
homeassistant:
  customize: !include customize.yaml
  allowlist_external_dirs:
    - /config/custom_components/ruuvitag-listener
```

**Note:** Don't include the starting "sensor:" thing twice to the configuration.yaml file.

## Where users can get help with your project ##
Code is supplied as is, you are on your own.

## Who maintains and contributes to the project ##
[Nerdaxic](https://github.com/Nerdaxic), whenever I feel like it. Don't hold your breath for updates but feel free to fork!

Free for non-commercial use.

If this helped you in a meaningful way, you can get me coffee through [PayPal](https://www.paypal.me/nerdaxic).
