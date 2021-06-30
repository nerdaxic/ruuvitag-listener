#!/usr/bin/python3
# coding=UTF-8
from ruuvitag_sensor.ruuvi import RuuviTagSensor, RunFlag
import json
import datetime
import argparse
import os, sys

# Make the paths work, not if code is run from crontab or directly from folder
path = os.path.abspath(os.path.dirname(__file__))

# List of files
sensor_list_json = path+"/sensor_list.json"
measurements_json = path+"/measurements.json"
config_file = path+"/configuration.txt"
customize_file = path+"/customization.txt"

# Read list of sensors
with open(sensor_list_json) as f:
    data = f.read()
sensors = json.loads(data)

# Load previous values from file to update
with open(measurements_json) as f:
    data = f.read()
previous_measurements = json.loads(data)

# Listen for RuuviTags for roughly 60 seconds
counter = 60
results = {}
results['measurements'] = []
results['time'] = []
number_of_sensors = len(sensors)

# RunFlag for stopping execution at desired time
run_flag = RunFlag()

# Process the sensors when match is found
def handle_data(found_data):
    global results
    global measurements_json
    global number_of_sensors
    global previous_measurements
    global counter

    # Ooh, a new measurement I haven't already heard in this session!
    if found_data[0] not in str(results['measurements']):
        print("FOUND:       "+str(round(found_data[1]["temperature"],1))+' C '+sensors[found_data[0]]+" sensor ("+found_data[0]+")")

        # No need to recycle old data, remove found sensor from list of previous measurements
        for found_sensor in previous_measurements["measurements"]:
            if found_sensor["mac"] == found_data[0]:
                previous_measurements["measurements"].remove(found_sensor)

        # One more sensor found, aka one less missing
        number_of_sensors = number_of_sensors - 1

        # Append measurement data to be written into the json file
        results['measurements'].append({
            'mac': found_data[0],
            'time': str(datetime.datetime.now()),
        'data': found_data[1],
    })

    counter = counter - 1

    # If time is up or all the sensors have been found
    if counter == 0 or number_of_sensors == 0:
        # Stopth
        run_flag.running = False

        # Add missing sensor's previous value back to measurement file
        # Flat line/ previous known value is better than Home Assistant reading 0 as value because data is missing.
        if number_of_sensors > 0:
            for previous_measurement in previous_measurements["measurements"]:
                results['measurements'].append(previous_measurement)
                print("MISSING:     "+sensors[previous_measurement["mac"]]+ " sensor ("+previous_measurement["mac"]+")")

        else:
            print("All sensors found.")

        # Save the measurement file
        with open(measurements_json, 'w') as outfile:
            json.dump(results, outfile)
            print("FINISHED:    Measurements saved to "+measurements_json)

# Check if user wants configs instead of data
parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config", action='store_true', help="Write configuration file")
parser.add_argument("-ab", "--absolute", action='store_true', help="Add absolute humidity sensors to config file")
parser.add_argument("-av", "--average", action='store_true', help="Add average temperature and humidity sensors to config file")
args = parser.parse_args()

# Definitely configs wanted
if args.config:
    with open(config_file, 'w') as outfile:
        outfile.write("# Do not add the top-most line if you have 'sensor:'' already defined in the configuration.yaml\n\n")  
        outfile.write("sensor:\n")

        with open(customize_file, 'w') as customfile:

            for sensor_mac in sensors:

                sensor_name = sensors[sensor_mac]
                entity = sensor_name.lower().replace(" ", "_")
                
                # Thermometer
                outfile.write("  - platform: file\n")

                outfile.write("    name: "+sensor_name+" temperature\n")
                outfile.write("    file_path: /config/custom_components/ruuvitag-listener/measurements.json\n")
                outfile.write("    value_template: \"{% for measurement in value_json.measurements %}{%- if measurement.mac == '"+sensor_mac+"' -%}{{ measurement.data.temperature }}{% endif %}{% endfor %}\"\n")
                outfile.write("    unit_of_measurement: '°C'\n\n")
                customfile.write("sensor."+entity+"_temperature:\n")
                customfile.write("  icon: mdi:thermometer\n")
                customfile.write("  device_class: temperature\n")
                
                # Relative humidity     
                outfile.write("  - platform: file\n")
                outfile.write("    name: "+sensor_name+" humidity\n")
                outfile.write("    file_path: /config/custom_components/ruuvitag-listener/measurements.json\n")
                outfile.write("    value_template: \"{% for measurement in value_json.measurements %}{%- if measurement.mac == '"+sensor_mac+"' -%}{{ measurement.data.humidity }}{% endif %}{% endfor %}\"\n")
                outfile.write("    unit_of_measurement: '% (RH)'\n\n")
                customfile.write("sensor."+entity+"_humidity:\n")
                customfile.write("  icon: mdi:water-percent\n")
                customfile.write("  device_class: humidity\n")

                # Air pressure
                outfile.write("  - platform: file\n")
                outfile.write("    name: "+sensor_name+" air pressure\n")
                outfile.write("    file_path: /config/custom_components/ruuvitag-listener/measurements.json\n")
                outfile.write("    value_template: \"{% for measurement in value_json.measurements %}{%- if measurement.mac == '"+sensor_mac+"' -%}{{ measurement.data.pressure }}{% endif %}{% endfor %}\"\n")
                outfile.write("    unit_of_measurement: 'hPa'\n\n")
                customfile.write("sensor."+entity+"_air_pressure:\n")
                customfile.write("  icon: mdi:gauge\n")
                customfile.write("  device_class: pressure\n")

                # Battery voltage                    
                outfile.write("  - platform: file\n")
                outfile.write("    name: "+sensor_name+" sensor battery\n")
                outfile.write("    file_path: /config/custom_components/ruuvitag-listener/measurements.json\n")
                outfile.write("    value_template: \"{% for measurement in value_json.measurements %}{%- if measurement.mac == '"+sensor_mac+"' -%}{{ measurement.data.battery/1000 }}{% endif %}{% endfor %}\"\n")
                outfile.write("    unit_of_measurement: 'V'\n\n")
                customfile.write("sensor."+entity+"_sensor_battery:\n")
                customfile.write("  icon: mdi:battery-90-bluetooth\n")
                customfile.write("  device_class: voltage\n")

                # Absolute humidity, good estimate from  negative 50 to plus 100 °C
                # Read more page 12: https://www.hatchability.com/Vaisala.pdf
                if args.absolute:
                    entity = sensor_name.lower().replace(" ", "_")
                    outfile.write("  - platform: template\n")
                    outfile.write("    sensors:\n")
                    outfile.write("      "+entity+"_humidity_absolute:\n")
                    outfile.write("        friendly_name: Absolute "+entity+" humidity\n")
                    outfile.write("        value_template: \"{{ ((2.16679*6.116441*10**(((7.591386*(states('sensor."+entity+"_temperature') | float))/((states('sensor."+entity+"_temperature') | float)+240.7263)))*(((states('sensor."+entity+"_humidity') | float))/(100))*100)/(273.15+(states('sensor."+entity+"_temperature') | float))) | round(2) }}\"\n")
                    outfile.write("        device_class: humidity\n")
                    outfile.write("        icon_template: 'mdi:water-percent'\n")
                    outfile.write("        unit_of_measurement: 'g/m³'\n\n")

            # Does user want the average sensors
            if args.average:

                temperature_template = ""
                humidity_template = ""

                # Loop through the sensors to add the values together
                for sensor_mac in sensors:
                    sensor_name = sensors[sensor_mac]
                    entity = sensor_name.lower().replace(" ", "_")

                    if temperature_template != "":
                        temperature_template += " + "
                    if humidity_template != "":
                        humidity_template += " + "

                    temperature_template += " states('sensor."+entity+"_temperature') | float "
                    humidity_template += " states('sensor."+entity+"_humidity') | float "

                outfile.write("  - platform: template\n")
                outfile.write("    sensors:\n")
                outfile.write("      average_temperature:\n")
                outfile.write("        friendly_name: 'Average indoor temperature'\n")
                # Take an average by deviding the sum with the number of sensors
                outfile.write("        value_template: \"{{ (("+temperature_template+") / "+str(number_of_sensors)+" ) | round(2) }}\"\n")
                outfile.write("        device_class: temperature\n")
                outfile.write("        icon_template: mdi:thermometer\n")
                outfile.write("        unit_of_measurement: '°C'\n\n")

                outfile.write("  - platform: template\n")
                outfile.write("    sensors:\n")
                outfile.write("      average_humidity:\n")
                outfile.write("        friendly_name: 'Average indoor humidity'\n")
                # Take an average by deviding the sum with the number of sensors
                outfile.write("        value_template: \"{{ (("+humidity_template+") / "+str(number_of_sensors)+" ) | round(2) }}\"\n")
                outfile.write("        device_class: humidity\n")
                outfile.write("        icon_template: 'mdi:water-percent'\n")
                outfile.write("        unit_of_measurement: '% (RH)'\n\n")

    print("FINISHED: Configuraion of "+str(number_of_sensors)+" Ruuvi-tags ("+str(number_of_sensors*4) + " Home Assistant sensors).")
    print("Please copy entries to configuration.yaml customizations to customize.yaml and restart Home Assistant.")
    print("CONFIGURATION: "+ config_file)
    print("CUSTOMIZATION: "+ customize_file)

# Actually measurement data wanted
else:
    print("Started listening...")
    RuuviTagSensor.get_datas(handle_data, sensors.keys(), run_flag)
