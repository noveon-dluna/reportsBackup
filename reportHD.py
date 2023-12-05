# This script is to create reports based on HD runs

#################################
# Importing Necessary Libraries #
#################################

import spareFunctions as sf
import datetime
import matplotlib.pyplot as plt
import secrets

 
#######################################
# Establishing connection to database #
#######################################

# Connection to SCADA database
cur = sf.cur
# Connection to UMCDB
umccur = sf.umccur

# Establishing a cutoff date for when database names change format
cutoffdate = '2021-12-31'

###########
# Tag IDs #
###########

# HD1 tag IDs
hdattributes_tagids1 = [{"name":"Vessel Pressure", "tagid":"5768"}, #16768
                        {"name":"Vessel Temperature", "tagid":"5778"},
                        {"name":"Speed (RPM)", "tagid":"5917"},
                        {"name":"Water In Temp", "tagid":"5776"},
                        {"name":"Water Out Temp", "tagid":"5777"},
                        {"name":"Total Active Power", "tagid":"5806"},
                        {"name":"Total Apparent Power", "tagid":"5809"},
                        {"name":"Total Reactive Power", "tagid":"5808"},
                        {"name":"Average Power Factor", "tagid":"5807"},
                        {"name":"Active Energy Import", "tagid":"5805"},
                        {"name":"Weather Station Temperature", "tagid":"17230"},
                        {"name":"Weather Station Relative Humidity", "tagid":"17229"},
                        {"name":"Weather Station Pressure", "tagid":"17226"},
                        {"name":"HD Platform Temperature", "tagid":"24399"},
                        {"name":"HD Platform Relative Humidity", "tagid":"24397"}]

# HD2 tag IDs
hdattributes_tagids2 = [{"name":"Vessel Pressure", "tagid":"14390"},
                        {"name":"Vessel Temperature", "tagid":"14351"},
                        {"name":"Speed (RPM)", "tagid":"5896"},
                        {"name":"Water In Temp", "tagid":"14370"},
                        {"name":"Water Out Temp", "tagid":"14380"},
                        {"name":"Total Active Power", "tagid":"17080"},
                        {"name":"Total Apparent Power", "tagid":"5809"},    # wrong tag ID
                        {"name":"Total Reactive Power", "tagid":"17093"},
                        {"name":"Average Power Factor", "tagid":"5807"},   # wrong tag ID
                        {"name":"Active Energy Import", "tagid":"17082"},
                        {"name":"Weather Station Temperature", "tagid":"17230"},
                        {"name":"Weather Station Relative Humidity", "tagid":"17229"},
                        {"name":"Weather Station Pressure", "tagid":"17226"},
                        {"name":"HD Platform Temperature", "tagid":"24399"},
                        {"name":"HD Platform Relative Humidity", "tagid":"24397"}]

# HD3 tag IDs
hdattributes_tagids3 = [{"name":"Vessel Pressure", "tagid":"13973"},
                        {"name":"Vessel Temperature", "tagid":"14034"},
                        {"name":"Speed (RPM)", "tagid":"6371"},
                        {"name":"Water In Temp", "tagid":"14029"},
                        {"name":"Water Out Temp", "tagid":"14040"},
                        {"name":"Total Active Power", "tagid":"17209"},
                        {"name":"Total Apparent Power", "tagid":"6374"},       # retired
                        {"name":"Total Reactive Power", "tagid":"17223"},
                        {"name":"Average Power Factor", "tagid":"6332"},        # retired
                        {"name":"Active Energy Import", "tagid":"17208"},       #either 17208 or 6330
                        {"name":"Weather Station Temperature", "tagid":"17230"},
                        {"name":"Weather Station Relative Humidity", "tagid":"17229"},
                        {"name":"Weather Station Pressure", "tagid":"17226"},
                        {"name":"HD Platform Temperature", "tagid":"24399"},
                        {"name":"HD Platform Relative Humidity", "tagid":"24397"}]       

                        # 17208 tagpath: _hdreactor3_/power monitoring/active energy import in 3 phases (kwh)
                        # 6330 tagpath: _hdreactor3_/active energy import in 3 phases (kwh)

# HD4 tag IDs
hdattributes_tagids4 = [{"name":"Vessel Pressure", "tagid":"14575"},
                        {"name":"Vessel Temperature", "tagid":"14536"},
                        {"name":"Speed (RPM)", "tagid":"5917"},
                        {"name":"Water In Temp", "tagid":"14555"},
                        {"name":"Water Out Temp", "tagid":"14565"},
                        {"name":"Total Active Power", "tagid":"24887"},
                        {"name":"Total Apparent Power", "tagid":"5809"},    # wrong tag ID
                        {"name":"Total Reactive Power", "tagid":"24890"},
                        {"name":"Average Power Factor", "tagid":"5807"},    # wrong tag ID
                        {"name":"Active Energy Import", "tagid":"24902"},
                        {"name":"Weather Station Temperature", "tagid":"17230"},
                        {"name":"Weather Station Relative Humidity", "tagid":"17229"},
                        {"name":"Weather Station Pressure", "tagid":"17226"},
                        {"name":"HD Platform Temperature", "tagid":"24399"},
                        {"name":"HD Platform Relative Humidity", "tagid":"24397"}]




############################
# Report Creation Function #
############################

def makeReport(runarray, filepath, pdf, reporttype, multiply=False):
    # Currently, do not know what the on-off tag ID is, so just use timestamp from equipment_runs as the start time
    # Make stop time just 3 hours after start time
    # Get all attributes data from between those 2 times
    # Make plots from that


    ###############
    # Multipliers #
    ###############

    # Creating a list of multipliers that will be randomly selected from throughout the script
    if multiply == True:
        multipliers = [1.23,0.69,1.07,0.84,1.45]
    else:
        multipliers = [1,1,1,1,1]

    # Selecting a random multiplier value that will be used for all temperature values for consistency
    tempmultiplier = multipliers[secrets.randbelow(5)]

    # Function that takes an array as input, and outputs a similar array that was multiplied by a random constant
    def obscure(array, type='normal'):

        # Choose one of the multipliers from the list above
        # On default, get a new value from the list of multipliers every time
        if type.lower() == 'normal':
            multiplier = multipliers[secrets.randbelow(5)]
        # If specified, the same multiplier can be used for consecutive arrays, so related data can be changed in similar amounts
        elif type.lower() == 'temperature':
            multiplier = tempmultiplier

        # Create the new multiplied array by multiplying part of each element of the original array by the multiplier
        multipliedarray = []
        for k in range(len(array)):
            subarray = array[k]
            subarray[1] = subarray[1] * multiplier
            multipliedarray.append(subarray)

        return multipliedarray


    ###########################
    # Getting Run Information #
    ###########################

    # Specifying batch ID until tied in with other scripts
    batchid = runarray[0][3]

    # Getting run information where the batch ID matches
    # Finding the starting timestamp from the input batch using SCADA.equipment_runs
    cur.execute("SELECT id, equipment_id, batch_id, product_id, employee_id, recipe_id, comment, timestamp FROM equipment_runs WHERE batch_id='{}' ORDER BY timestamp DESC".format(batchid))
    runinfo = sf.makeArray(cur.fetchall())

    # If the batch number corresponds to multiple entries in the table, then print a message saying so, and use the first entry
    if len(runinfo) > 1:
        print('Multiple entries in SCADA.equipment_runs for batch ID {}. The most recent run will be used'.format(batchid))
    
    runinfo = runinfo[0]

    # Get additional run information from the tables below, unless the batch number does not exist elsewhere
    try:
        # Getting quantity and comments
        cur.execute("SELECT weight, weight_type FROM equipment_run_weights WHERE equipment_run_id='{}'".format(runinfo[0]))
        results = sf.makeArray(cur.fetchall())[0]
        if len(results) > 0:
            runinfo.append(results[0])
            runarray[0][5].append(results[0])
        else:
            runinfo = runinfo + ['Missing'] * 2
            runarray[0][5].append('Missing')
    except:
        runinfo = runinfo + ['Missing'] * 2
        runarray[0][5].append('Missing')


    # Getting previous batch IDs, which are listed as component_batch_id
    try:
        umccur.execute("SELECT component_batch_id FROM batch_inputs WHERE batch_id='{}'".format(batchid))
        prevbatchresults = sf.makeArray(umccur.fetchall())[0]
        for element in prevbatchresults:
            runinfo.append(element)
    except:
        runinfo = runinfo + ['Missing']


    # Getting the correct equipment name based on the equipment_id entry in SCADA.equipment_runs table
    cur.execute("SELECT name, nvn_eq_id, process_id FROM equipment WHERE id={}".format(runinfo[1]))
    results = sf.makeArray(cur.fetchall())[0]
    runinfo.append(results[1] + ' (' + results[0] + ')')    # Combining the nvn_eq_id and name into one entry
    runinfo.append(results[2])                            # Adding the process_id to the runinfo array

    # Determining what date the batch was run in, in the format of YYYY-MM-DD
    day = runinfo[7].strftime("%Y-%m-%d")
    month = day[5:7]
    year = day[0:4]


    # If the day is on or before the cutoff date, then change the database name to the appropriate year
    if day <= cutoffdate:
        database = 'SCADA_' + year
    else:
        database = 'SCADA_' + year + '_' + month

    print('Starting time is: {}'.format(runinfo[7]))

        
    # Getting a starting table from the date in runinfo
    starttable = database + '.sqlt_data_1_' + datetime.datetime.strftime(runinfo[7], "%Y%m%d")
    tables = [starttable]

    # Creating a timestamp from the datetime listed in the hd run table eq_hds
    starttime = runinfo[7].timestamp() * 1000

    # Adding 3 hours to the starttime, and calling it the stoptime
    stoptime = starttime + 3600000*3

    print('Stop time is: {}'.format(datetime.datetime.fromtimestamp(stoptime/1000)))

    # Establishing the total amount of time the equipment ran for
    totalruntime = datetime.datetime.fromtimestamp(stoptime/1000) - datetime.datetime.fromtimestamp(starttime/1000)

    # Finding the correct tag IDs based on the equipment ID
    equipmentid = runinfo[1]
    if equipmentid == 27:
        hdattributes_tagids = hdattributes_tagids1
    elif equipmentid == 28:
        hdattributes_tagids = hdattributes_tagids2
    elif equipmentid == 29:
        hdattributes_tagids = hdattributes_tagids3
    elif equipmentid == 30:
        hdattributes_tagids = hdattributes_tagids4
    


    # Now get data from SCADA database between start and stop times
    hdattributes = []
    for element in hdattributes_tagids:

        # First changing the tag ID to include all related tag IDs to account for any being retired
        element["tagid"] = sf.getAllTags(element["tagid"])

        subarray = []
        for table in tables:
            cur.execute("SELECT tagid, intvalue, floatvalue, stringvalue, datevalue, t_stamp FROM {} WHERE tagid IN ({}) AND t_stamp > {} AND t_stamp < {} ORDER BY t_stamp ASC".format(table,element["tagid"],starttime,stoptime))
            array = sf.makeArray(cur.fetchall(),removeNone=True)
            subarray = subarray + array

        if element['tagid'] == '5776' or element['tagid'] == '5777' or element['tagid'] == '5778':
            obscure(subarray, type='temperature')
        else:
            obscure(subarray)

        hdattributes.append(subarray)

    # Determining how much energy was used from start to end
    try:
        totalenergy = round(hdattributes[9][-1][1] - hdattributes[9][0][1],1) # kWh
    except:
        totalenergy = 'Missing'


    ##################
    # Creating plots #
    ##################

    # Setting a font size to be used in all the graphs for uniformity
    font_size=12


    ###################################
    # Vessel Pressure and temperature #
    ###################################

    def hdPressure(pdf,halfsize=False, xadjust=0,yadjust=0):

        try:
            # Plotting pressure, temperature, and RPM throughout the run
            fig, ax1 = plt.subplots(figsize=(10,6))
            ax1.grid(linestyle='--', linewidth=1)
            ax2 = ax1.twinx()
            ax3 = ax1.twinx()

            # Offsetting the axes so that they do not overlap
            ax3.spines["right"].set_position(("axes",1.12))

            ax1.plot([(x[2] - starttime)/3600000 for x in hdattributes[0]],[x[1] for x in hdattributes[0]],color='black',label = 'Pressure')
            ax2.plot([(x[2] - starttime)/3600000 for x in hdattributes[2]],[x[1] for x in hdattributes[2]],color='red',label = 'Speed')
            ax3.plot([(x[2] - starttime)/3600000 for x in hdattributes[1]],[x[1] for x in hdattributes[1]],color='green',label = 'Temperature')

            # Plotting empty arrays to ax1 just so that the legend will have everything
            ax1.plot([],[],color='red',label = 'Speed')
            ax1.plot([],[],color='green',label = 'Temperature')

            ax1.set_ylabel('Pressure (mbar)', fontsize=font_size)
            ax1.set_xlabel('Time Elapsed (Hours)',fontsize=font_size)
            ax2.set_ylabel('Speed (rpm)', fontsize=font_size)
            ax3.set_ylabel('Temp (C)', fontsize=font_size)

            legend = ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1),
                    fancybox=True, shadow=True, ncol=3)

            plt.savefig(filepath + 'hdpressure.png',bbox_inches='tight')
            ax1.clear()
            ax2.clear()
            ax3.clear()
            plt.cla()

            # Add plot to PDF
            sf.addPlot(pdf, 'Vessel Pressure and Temperature',filepath + 'hdpressure.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust)

        except:
            # Printing to the PDF that there was an error
            sf.writeHeader(pdf,'Vessel Pressure and Temperature',halfsize=halfsize)
            pdf.write(10, 'Unable to create Vessel Pressure and Temperature plot.\n\n')
            # Printing to the console
            print('Unable to create Vessel Pressure and Temperature plot.\n')


    #############################
    # Cooling water temperature #
    #############################

    def hdWaterTemp(pdf,halfsize=False,xadjust=0,yadjust=0):

        try:
            # Plotting water in temp and water out temp
            fig, ax1 = plt.subplots(figsize=(10,6))
            ax1.grid(linestyle='--', linewidth=1)

            ax1.plot([(x[2] - starttime)/3600000 for x in hdattributes[3]],[x[1] for x in hdattributes[3]],label = 'Water In Temp')
            ax1.plot([(x[2] - starttime)/3600000 for x in hdattributes[4]],[x[1] for x in hdattributes[4]],label = 'Water Out Temp')

            ax1.set_ylabel('Temperature (C)', fontsize=font_size)
            ax1.set_xlabel('Time Elapsed (Hours)',fontsize=font_size)

            legend = ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1),
                                fancybox=True, shadow=True, ncol=2)
            
            plt.savefig(filepath + 'hdwatertemp.png',bbox_inches='tight')
            ax1.clear()
            plt.cla()

            # Add plot to the PDF
            sf.addPlot(pdf, 'Cooling Water Temperature', filepath + 'hdwatertemp.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust)

        except:
            # Printing to the PDF that there was an error
            sf.writeHeader(pdf,'Cooling Water Temperature',halfsize=halfsize)
            pdf.write(10, 'Unable to create Cooling Water Temperature plot.\n\n')
            # Printing to the console
            print('Unable to create Cooling Water Temperature plot.\n')


    #################
    # Reactor power #
    #################

    def hdPower(pdf, halfsize=False, xadjust=0, yadjust=0):

        try:
            # Creating the figure
            fig, ax1 = plt.subplots(figsize=(10,6))
            ax1.grid(linestyle='--', linewidth=1)
            ax2 = ax1.twinx()
            ax3 = ax1.twinx()
            ax4 = ax1.twinx()

            # Offsetting the axes so that they do not overlap
            ax3.spines["right"].set_position(("axes",1.12))
            ax4.spines["left"].set_position(("axes",-0.12))
            ax4.spines["left"].set_visible(True)
            ax4.yaxis.set_label_position('left')
            ax4.yaxis.set_ticks_position('left')

            # Putting plots on the figure
            ax1.plot([(x[2] - starttime)/3600000 for x in hdattributes[5]],[x[1] for x in hdattributes[5]],color='blue',label = 'Total Active Power')
            ax2.plot([(x[2] - starttime)/3600000 for x in hdattributes[6]],[x[1] for x in hdattributes[6]],color='black',label = 'Total Apparent Power')
            ax3.plot([(x[2] - starttime)/3600000 for x in hdattributes[7]],[x[1] for x in hdattributes[7]],color='red',label = 'Total Reactive Power')
            ax4.plot([(x[2] - starttime)/3600000 for x in hdattributes[8]],[x[1] for x in hdattributes[8]],color='green',label = 'Average Power Factor')

            # Plotting empty arrays to ax1 just so that the legend will have everything
            ax1.plot([],[],color='black',label = 'Total Apparent Power')
            ax1.plot([],[],color='red',label = 'Total Reactive Power')
            ax1.plot([],[],color='green',label = 'Average Power Factor')

            # Taking care of labeling
            ax1.set_xlabel('Time Elapsed (Hours)', fontsize=font_size)
            ax1.set_ylabel('Active Power (W)', fontsize=font_size)
            ax2.set_ylabel('Apparent Power (kva)', fontsize=font_size)
            ax3.set_ylabel('Reactive Power (var)', fontsize=font_size)
            ax4.set_ylabel('Avg Power Factor', fontsize=font_size)

            legend = ax1.legend(loc='upper center', bbox_to_anchor=(0.5,-0.1),
                                fancybox=True, shadow=True, ncol=2)
            
            # Saving figure and clearing everything
            plt.savefig(filepath + 'hdPower.png', bbox_inches='tight')
            ax1.clear()
            ax2.clear()
            ax3.clear()
            ax4.clear()
            plt.cla()

            # Add plot to the PDF
            sf.addPlot(pdf, 'Reactor Power', filepath + 'hdPower.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust)

        except:
            # Printing to the PDF that there was an error
            sf.writeHeader(pdf,'Reactor Power',halfsize=halfsize)
            pdf.write(10, 'Unable to create Reactor Power plot.\n\n')
            # Printing to the console
            print('Unable to create Reactor Power plot.\n')


    ##################
    # Reactor energy #
    ##################

    def hdEnergy(pdf, halfsize=False, xadjust=0, yadjust=0):

        try:
            # Creating the figure
            fig, ax1 = plt.subplots(figsize=(10,6))
            ax1.grid(linestyle='--', linewidth=1)

            # Putting plot on the figure
            ax1.plot([(x[2] - starttime)/3600000 for x in hdattributes[9]],[x[1] for x in hdattributes[9]],label = 'Active Energy Import')
            
            ax1.set_xlabel('Time Elapsed (Hours)', fontsize=font_size)
            ax1.set_ylabel('Energy (kWh)', fontsize=font_size)

            legend = ax1.legend(loc='upper center', bbox_to_anchor=(0.5,-0.1),
                                fancybox=True, shadow=True, ncol=1)
            
            # Saving figure and clearing everything
            plt.savefig(filepath + 'hdEnergy.png', bbox_inches='tight')
            ax1.clear()
            plt.cla()

            # Adding plot to the PDF
            sf.addPlot(pdf, 'Reactor Energy', filepath + 'hdEnergy.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust)

        except:
            # Printing to the PDF that there was an error
            sf.writeHeader(pdf,'Reactor Energy',halfsize=halfsize)
            pdf.write(10, 'Unable to create Reactor Energy plot.\n\n')
            # Printing to the console
            print('Unable to create Reactor Energy plot.\n')


    ####################
    # Weather Stations #
    ####################

    def outdoorWeatherStation(pdf, halfsize=False, xadjust=0, yadjust=0):

        try:
            # Creating the figure
            fig, ax1 = plt.subplots(figsize=(10,6))
            ax1.grid(linestyle='--', linewidth=1)
            ax2 = ax1.twinx()
            ax3 = ax1.twinx()

            # Offsetting the axes so that they do not overlap
            ax3.spines["right"].set_position(("axes",1.12))

            # Putting plot on the figure
            ax1.plot([(x[2] - starttime)/3600000 for x in hdattributes[10]],[x[1] for x in hdattributes[10]],color='blue',label = 'Temperature')
            ax2.plot([(x[2] - starttime)/3600000 for x in hdattributes[11]],[x[1] for x in hdattributes[11]],color='black',label = 'Relative Humidity')
            ax3.plot([(x[2] - starttime)/3600000 for x in hdattributes[12]],[x[1] for x in hdattributes[12]],color='red',label = 'Barometric Pressure')

            # Plotting empty arrays to ax1 just so that the legend will have everything
            ax1.plot([],[],color='black',label = 'Relative Humidity')
            ax1.plot([],[],color='red',label = 'Barometric Pressure')
            
            # Setting axis labels
            ax1.set_xlabel('Time Elapsed (Hours)', fontsize=font_size)
            ax1.set_ylabel('Temperature (C)', fontsize=font_size)
            ax2.set_ylabel('Humidity (%)', fontsize=font_size)
            ax3.set_ylabel('Pressure (mbar)', fontsize=font_size)
            ax3.ticklabel_format(style='plain')

            legend = ax1.legend(loc='upper center', bbox_to_anchor=(0.5,-0.1),
                                fancybox=True, shadow=True, ncol=3)
            
            # Saving figure and clearing everything
            plt.savefig(filepath +'outdoorWeather.png', bbox_inches='tight')
            ax1.clear()
            ax2.clear()
            ax3.clear()
            plt.cla()

            # Adding header to the PDF
            sf.writeHeader(pdf,'Outdoor Weather Station',halfsize=halfsize)
            pdf.ln(5)
            
            # Creating a table under the header (only half a page wide) that will contain the date/time of the first reading, the first temperature reading, and the first humidity reading
            # Column titles will be Date/Time, Temperature (C), and Humidity (%) respectively
            pdf.set_font('Helvetica', 'B', 10)
            pdf.cell(40, 6, 'Date/Time', 1, 0, 'C')
            pdf.cell(40, 6, 'Temperature (C)', 1, 0, 'C')
            pdf.cell(40, 6, 'Humidity (%)', 1, 0, 'C')
            pdf.cell(40, 6, 'Pressure (mbar)', 1, 1, 'C')
            pdf.set_font('Helvetica', '', 10)
            pdf.cell(40, 6, datetime.datetime.fromtimestamp(hdattributes[10][0][2]/1000).strftime('%Y-%m-%d %H:%M:%S'), 1, 0, 'C')
            pdf.cell(40, 6, str(round(hdattributes[10][0][1],2)), 1, 0, 'C')
            pdf.cell(40, 6, str(round(hdattributes[11][0][1],2)), 1, 0, 'C')
            pdf.cell(40, 6, str(round(hdattributes[12][0][1],2)), 1, 1, 'C')

            # Adding plot to the PDF
            sf.addPlot(pdf, 'Outdoor Weather Station', filepath + 'outdoorWeather.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust, header=False)

        except:
            # Printing to the PDF that there was an error
            pdf.write(10, 'Unable to create Outdoor Weather Station plot.\n\n')
            # Printing to the console
            print('Unable to create Outdoor Weather Station plot.\n')

    
    def indoorWeatherStation(pdf, halfsize=False, xadjust=0, yadjust=0):

        try:
            # Creating the figure
            fig, ax1 = plt.subplots(figsize=(10,6))
            ax1.grid(linestyle='--', linewidth=1)
            ax2 = ax1.twinx()

            # Putting plot on the figure
            ax1.plot([(x[2] - starttime)/3600000 for x in hdattributes[13]],[x[1] for x in hdattributes[13]],color='blue',label = 'Temperature')
            ax2.plot([(x[2] - starttime)/3600000 for x in hdattributes[14]],[x[1] for x in hdattributes[14]],color='black',label = 'Relative Humidity')

            # Plotting empty arrays to ax1 just so that the legend will have everything
            ax1.plot([],[],color='black',label = 'Relative Humidity')
            ax1.plot([],[],color='red',label = 'Barometric Pressure')
            
            # Setting axis labels
            ax1.set_xlabel('Time Elapsed (Hours)', fontsize=font_size)
            ax1.set_ylabel('Temperature (C)', fontsize=font_size)
            ax2.set_ylabel('Humidity (%)', fontsize=font_size)


            legend = ax1.legend(loc='upper center', bbox_to_anchor=(0.5,-0.1),
                                fancybox=True, shadow=True, ncol=3)
            
            # Saving figure and clearing everything
            plt.savefig(filepath +'indoorWeather.png', bbox_inches='tight')
            ax1.clear()
            ax2.clear()
            plt.cla()

            # Adding header to the PDF
            sf.writeHeader(pdf,'Indoor Weather Station',halfsize=halfsize)
            pdf.ln(5)
            
            # Creating a table under the header (only half a page wide) that will contain the date/time of the first reading, the first temperature reading, and the first humidity reading
            # Column titles will be Date/Time, Temperature (C), and Humidity (%) respectively
            pdf.set_font('Helvetica', 'B', 10)
            pdf.cell(40, 6, 'Date/Time', 1, 0, 'C')
            pdf.cell(40, 6, 'Temperature (C)', 1, 0, 'C')
            pdf.cell(40, 6, 'Humidity (%)', 1, 1, 'C')
            pdf.set_font('Helvetica', '', 10)
            pdf.cell(40, 6, datetime.datetime.fromtimestamp(hdattributes[13][0][2]/1000).strftime('%Y-%m-%d %H:%M:%S'), 1, 0, 'C')
            pdf.cell(40, 6, str(round(hdattributes[13][0][1],2)), 1, 0, 'C')
            pdf.cell(40, 6, str(round(hdattributes[14][0][1],2)), 1, 1, 'C')

            # Adding plot to the PDF
            sf.addPlot(pdf, 'Indoor Weather Station', filepath + 'indoorWeather.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust, header=False)

        except:
            # Printing to the PDF that there was an error
            pdf.write(10, 'Unable to create Indoor Weather Station plot.\n\n')
            # Printing to the console
            print('Unable to create Indoor Weather Station plot.\n')


    ##########################        
    # Write in batch details #
    ##########################
    
    def batchDetails(pdf):
        # Writing in batch details
        pdf.set_font('Helvetica', '', 10)
        pdf.multi_cell(55,5.5,'Batch ID')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-6.5)
        pdf.multi_cell(85,5.5,runarray[0][3])
        pdf.multi_cell(55,5.5,'Product ID')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-6.5)
        pdf.multi_cell(85,5.5,str(runarray[0][4]) + ' (' + sf.productType(runarray[0][4]) + ')')
        pdf.multi_cell(55,5.5,'Output Quantity (Dashboard)')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-6.5)
        pdf.multi_cell(85,5.5,runarray[0][5][0])
        pdf.multi_cell(55,5.5,'Output Quantity (Transfer Bottles)')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-6.5)
        pdf.multi_cell(85,5.5,runarray[0][5][1])
        pdf.multi_cell(55,5.5,'Output Quantity (HMI)')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-6.5)
        pdf.multi_cell(85,5.5,str(runarray[0][5][2]))
        pdf.multi_cell(55,5.5,'Operator ID')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-6.5)
        pdf.multi_cell(85,5.5,runarray[0][8])
        pdf.multi_cell(55,5.5,'Description')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-6.5)
        pdf.multi_cell(135,5.5,runarray[0][7])
        pdf.multi_cell(55,5.5,'Equipment')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-6.5)
        pdf.multi_cell(105,5.5,runarray[0][9] + ' (ID: ' + runarray[0][2] + ')')
        pdf.multi_cell(55,5.5,'Date')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-6.5)
        pdf.multi_cell(105,5.5,str(runarray[0][6]))
        pdf.multi_cell(55,5.5,'Total Run Time')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-6.5)
        pdf.multi_cell(85,5.5,str(totalruntime))
        pdf.multi_cell(55,5.5,'Energy Used')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-6.5)
        pdf.multi_cell(85,5.5,str(totalenergy) + ' kWh')
        pdf.multi_cell(55,5.5,'Multiplier Applied?')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        if multiply == True:
            pdf.multi_cell(85,5.5,'Yes')
        else:
            pdf.multi_cell(85,5.5,'No')


    #################################
    # Adding sections to the report #
    #################################

    # Adding sections to the PDF for singular report
    def addSingular(pdf):

        # Creating a new page and header for the beginning of the report
        pdf.add_page()
        pdf.set_font('Helvetica', 'b', 16)
        pdf.ln(5)
        pdf.write(5, 'HD Report')
        pdf.ln(8)

        # Adding in batch details
        batchDetails(pdf)

        # Transfer bottle information
        sf.transferBottles(batchid=batchid, pdf=pdf)

        # Adding in the plots
        pdf.add_page()
        hdPressure(pdf)
        hdWaterTemp(pdf)
        hdPower(pdf)
        hdEnergy(pdf)

        # Adding in the list of tag IDs that were used to gather data
        sf.addTags(hdattributes_tagids, pdf=pdf)

        # Closing all figures so that they don't stay open and take up memory
        plt.close('all')


    # Adding sections to the PDF for comprehensive report
    def addComprehensive(pdf):

        # Creating a new page and header for each report added to this bigger report
        pdf.add_page()
        pdf.set_font('Helvetica', 'b', 16)  
        pdf.ln(5)
        pdf.write(5, 'Process ' + str(runarray[0][0]) + ' - ' + str(runarray[0][1]))
        pdf.ln(8)

        # Adding in batch details
        batchDetails(pdf)

        # Transfer bottle information
        sf.transferBottles(batchid=batchid, pdf=pdf)
        pdf.add_page()
        
        # Adding in the plots
        if pdf.get_y() > 200:
            pdf.add_page()

        ybefore = pdf.get_y()
        hdPressure(pdf=pdf, halfsize=True)

        pdf.set_y(ybefore)
        hdWaterTemp(pdf=pdf, halfsize=True, xadjust=90)

        ybefore = pdf.get_y()
        hdPower(pdf=pdf, halfsize=True)
        if ybefore > 200:
            pdf.set_y(10)
        else:
            pdf.set_y(ybefore)

        hdEnergy(pdf=pdf, halfsize=True, xadjust=90)

        pdf.add_page()

        indoorWeatherStation(pdf=pdf, halfsize=True)
        outdoorWeatherStation(pdf=pdf, halfsize=True)

        # Adding in the list of tag IDs that were used to gather data
        sf.addTags(hdattributes_tagids, pdf=pdf)

        # Closing all figures so that they don't stay open and take up too much memory if function is called multiple times
        plt.close('all')

    
    # Adding sections to the PDF for customer report
    def addCustomer(pdf):

        # Creating a header for each equipment report added to the larger customer report
        pdf.set_font('Helvetica', 'b', 16)
        pdf.ln(5)
        pdf.write(5, 'Process ' + str(runarray[0][0]) + ' - ' + str(runarray[0][1]))
        pdf.ln(8)

        # Adding in batch details
        batchDetails(pdf)

        # Adding in some space at the end
        pdf.ln(10)
        

    # Adding sections to the PDF based on whether report type is comprehensive or singular
    if reporttype == 'singular':
        addSingular(pdf)
    elif reporttype == 'comprehensive':
        addComprehensive(pdf)
    elif reporttype == 'customer':
        addCustomer(pdf)
