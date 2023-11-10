# This script is to create reports based on runs in the Jet Mill

#################################
# Importing Necessary Libraries #
#################################

import spareFunctions as sf
import matplotlib.pyplot as plt
import datetime
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


# Making a list of tag IDs that will need to be looked at
jmattributes_tagids = [{"name":"Spindle RPM", "tagid":"4936"},
                    {"name":"Compressor Outlet Pressure", "tagid":"5857"},
                    {"name":"Bottom Nozzle Pressure", "tagid":"5840"},
                    {"name":"Grinding Chamber Weight", "tagid":"5871"},
                    {"name":"Grinding Chamber Temp", "tagid":"5828"},
                    {"name":"Spindle Front Temp", "tagid":"5827"},
                    {"name":"Spindle Rear Temp", "tagid":"4932"},
                    {"name":"Compressor Water Out Temp", "tagid":"5837"},
                    {"name":"Heat Ex Out Temp", "tagid":"5831"},
                    {"name":"02 Sensor 1", "tagid":"5868"},
                    {"name":"02 Sensor 2", "tagid":"5869"},
                    {"name":"02 Sensor 3", "tagid":"5870"},
                    {"name":"Dew Point Sensor", "tagid":"6626"},
                    {"name":"Vibration Sensor VS1303", "tagid":"6040"},
                    {"name":"Vibration Sensor VS1304", "tagid":"6460"},
                    {"name":"Vibration Sensor VS1305", "tagid":"6461"},
                    {"name":"Total Active Power JM", "tagid":"6167"},
                    {"name":"Total Apparent Power JM", "tagid":"6169"},
                    {"name":"Total Active Energy Import JM", "tagid":"6172"},
                    {"name":"Total Apparent Power Compressor", "tagid":"37332"},     # Either 6293 or 37332
                    {"name":"Total Active Power Compressor", "tagid":"37325"},       # Either 6291 or 37325
                    {"name":"Total Active Energy Compressor", "tagid":"37331"},      # Either 6288 or 37331
                    {"name":"Weather Station Temperature", "tagid":"17230"},
                    {"name":"Weather Station Relative Humidity", "tagid":"17229"},
                    {"name":"Weather Station Pressure", "tagid":"17226"},
                    {"name":"HD Platform Temperature", "tagid":"24399"},
                    {"name":"HD Platform Relative Humidity", "tagid":"24397"}]      



###################################
# Defining Functions for PSA Runs #
###################################

# Defining a function to get run information
def getpsaRun(batchid):

    cur.execute("SELECT id, batch_id, sample_no, operator, timestamp, comments FROM eq_psa_runs WHERE batch_id='{}' ORDER BY timestamp ASC".format(batchid))
    psaruninfo = sf.makeArray(cur.fetchall())

    if len(psaruninfo) > 1:
        print('\nMultiple PSA runs were performed for the same batch ID {}.\n Only the most recent run will be used.'.format(batchid))

    # Only using the most recent run
    psaruninfo = psaruninfo[-1:]

    return psaruninfo


# Defining a function to get run settings
def getpsaSettings(psaruninfo):
    psasettings = []

    for run in psaruninfo:
        runID = run[0]
        cur.execute("SELECT * FROM eq_psa_run_settings WHERE eq_psa_run_id={}".format(runID))
        results = sf.makeArray(cur.fetchall())
        psasettings.append(results)

    return psasettings


# Defining a function to get standard values
def getStandards(psaruninfo):
    psarunstandards = []

    for run in psaruninfo:
        runID = run[0]
        cur.execute("SELECT * FROM eq_psa_run_svalues WHERE eq_psa_run_id={} ORDER BY eq_psa_measurement_id DESC LIMIT 1".format(runID))
        results = sf.makeArray(cur.fetchall())

        # Rounding to 4 decimal places
        for i in range(len(results)):
            for j in range(3,len(results[i])):
                results[i][j] = round(float(results[i][j]),4)
    
        psarunstandards.append(results)

    return psarunstandards


# Defining a function to get measurement values
def getpsaMeasurements(psaruninfo):
    psameasurements = []

    for run in psaruninfo:
        runID = run[0]
        cur.execute("SELECT eq_psa_run_id, eq_psa_measurement_id, size, volume, volume_cumulative FROM eq_psa_run_measurements WHERE eq_psa_run_id={} \
                     AND eq_psa_measurement_id=(SELECT MAX(eq_psa_measurement_id) FROM eq_psa_run_measurements WHERE eq_psa_run_id={})".format(runID,runID))
        results = sf.makeArray(cur.fetchall())
        psameasurements.append(results)

        print(psameasurements[0][0])

    return psameasurements


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

    # Determining batch ID from input
    batchid = runarray[0][3]

    # Getting run information where the batch ID matches
    cur.execute("SELECT id, equipment_id, batch_id, product_id, employee_id, recipe_id, comment, timestamp FROM equipment_runs WHERE batch_id='{}' ORDER BY timestamp ASC".format(batchid))
    runinfo = sf.makeArray(cur.fetchall())

    if len(runinfo) > 1:
        print('There have been multiple Jet Mill runs with the same batch ID {}'.format(batchid))

    for run in runinfo:
        print(run)

    # Establishing the first run done with this batch
    firstrun = runinfo[0]

    print('Starting time is: {}'.format(firstrun[7]))

    # Determining what date the batch was run in, in the format of YYYY-MM-DD
    day = firstrun[7].strftime("%Y-%m-%d")
    month = day[5:7]
    year = day[0:4]

    # If the day is before the cutoff date, then change the database name to the appropriate year
    if firstrun[7].strftime("%Y-%m-%d") <= cutoffdate:
        database = 'SCADA_' + year
    else:
        database = 'SCADA_' + year + '_' + month

    # Getting a starting table from the date in firstrun
    starttable = database + '.sqlt_data_1_' + datetime.datetime.strftime(firstrun[7], "%Y%m%d")
    tables = [starttable]

    # Adding another table to the list of tables from the day before the start day
    tables.insert(0,database + '.sqlt_data_1_' + (datetime.datetime.strptime(datetime.datetime.strftime(firstrun[7], "%Y%m%d"), "%Y%m%d") - datetime.timedelta(days=1)).strftime("%Y%m%d"))

    # Creating a timestamp from the datetime listed in the hd run table eq_hds
    starttime = int(datetime.datetime.timestamp(firstrun[7])*1000)

    # If there were multiple runs, then the stoptime will be 2 hours after the last start time
    if len(runinfo) > 1:
        lastrun = runinfo[-1]
        stoptime = int(datetime.datetime.timestamp(lastrun[7])*1000) + 3600000*2
    else:
        # Adding 2 hours to the starttime of the first run, and calling it the stoptime
        stoptime = starttime + 3600000*2

    print('Stop time is: {}'.format(datetime.datetime.fromtimestamp(stoptime/1000)))

    # Establishing the total run time for the equipment
    totalruntime = datetime.datetime.fromtimestamp(stoptime/1000) - datetime.datetime.fromtimestamp(starttime/1000)

    # If the stop time is on a different day than the start time, then add all tables from start day to stop day
    if datetime.datetime.fromtimestamp(stoptime/1000).strftime("%Y-%m-%d") != datetime.datetime.fromtimestamp(starttime/1000).strftime("%Y-%m-%d"):
        # Creating a list of dates between the start and stop times
        dates = []
        for i in range(1, (stoptime - starttime)//86400000 + 1):
            dates.append(datetime.datetime.fromtimestamp(starttime/1000) + datetime.timedelta(days=i))

        # Creating a list of tables to query based on the dates
        for date in dates:
            tables.append(database + '.sqlt_data_1_' + date.strftime('%Y%m%d'))

    # Now get data from SCADA database between start and stop times
    jmattributes = []
    for element in jmattributes_tagids:

        # First changing the tag ID to include all related tag IDs to account for any being retired
        element["tagid"] = sf.getAllTags(element["tagid"])

        subarray = []

        for table in tables:
            cur.execute("SELECT tagid, intvalue, floatvalue, stringvalue, datevalue, t_stamp FROM {} WHERE tagid IN ({}) AND t_stamp > {} AND t_stamp < {} ORDER BY t_stamp ASC".format(table,element["tagid"],starttime,stoptime))
            array = sf.makeArray(cur.fetchall(),removeNone=True)
            subarray = subarray + array

        obscure(subarray)
        jmattributes.append(subarray)

    # Finding the total energy used
    try:
        totalenergyjm = round(jmattributes[18][-1][1] - jmattributes[18][0][1],1) # kVAh
    except:
        totalenergyjm = 0
    try:
        totalenergycomp = round(jmattributes[21][-1][1] - jmattributes[21][0][1],1) # kVAh
    except:
        totalenergycomp = 0


    #################################
    # Getting the recipe parameters #
    #################################

    def recipeParameters(recipeid, pdf=pdf):

        # Getting the recipe parameters from the database
        cur.execute("SELECT a.param_id, a.intvalue, a.floatvalue, a.stringvalue, a.datevalue, \
                    b.name FROM equipment_recipe_values a INNER JOIN equipment_params b ON \
                    a.param_id = b.id WHERE recipe_id={}".format(recipeid))
        parameters = sf.makeArray(cur.fetchall(), removeNone=True)

        # Getting the name of the recipe
        cur.execute("SELECT name FROM equipment_recipes WHERE id={}".format(recipeid))
        recipename = cur.fetchone()[0]

        # If the parameter name begins with "HMI/Scada recipe ", then remove that part of the name and capitalize the first letter of the remaining portion
        for element in parameters:
            if element[2][0:16] == 'HMI/Scada recipe':
                element[2] = element[2][17:].capitalize()

        # Adding the recipe parameters to the PDF
        # First creating a header
        pdf.ln(10)
        sf.writeHeader(pdf,'Recipe Parameters',ignoremaxy=True)
        pdf.ln(5)

        # Then adding the recipe number and name
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(80, 6, 'Recipe Number: ', 0, 0, 'L')
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(80, 6, str(recipeid) + ': ' + recipename, 0, 1, 'L')

        # Then adding the parameters
        for element in parameters:
            # First writing the parameter name in bold, and then the value not bold
            pdf.set_font('Helvetica', 'B', 10)
            pdf.cell(80, 6, element[2] + ': ', 0, 0, 'L')
            pdf.set_font('Helvetica', '', 10)
            pdf.cell(80, 6, str(element[1]), 0, 1, 'L')

        # Adding a new page afterwards
        pdf.add_page()





    ###############################
    # Getting PSA run information #
    ###############################

    # Getting the run information for the PSA run from functions defined earlier
    try:
        psaRunInfo = getpsaRun(batchid)
        psaSettings = getpsaSettings(psaRunInfo)
        psaRunStandards = getStandards(psaRunInfo)
        psaMeasurements = getpsaMeasurements(psaRunInfo)
    except:
        psaRunInfo = []
        psaSettings = []
        psaRunStandards = []
        psaMeasurements = []

    # Creating headers for the tables that will be created. Headers will be column names from database
    runsettingsheader = ['Instrument','Lens','Feeder','Purge','Gain','Part. Ref Index','Media Ref. Index',
                         'Part. Density','Path Length','Mesh Factor','Scat Start','Scat. Threshold',
                         'Min Size','Max Size','Multiple Scat.']
    
    runstandardsheader = ['Trans','CV','SSA','DV (10)','DV (50)','DV (90)','Span',
                          'SMD  (D[3][2])','VMD  (D[4][3])']


    ##################
    # Creating plots #
    ##################

    # Setting a font size to be used in all the graphs for uniformity
    font_size=12


    ############
    # Overview #
    ############

    # Jet Mill overview (RPM, pressure, grinding chamber weight and temp)
    def jmOverview(pdf,halfsize=False, xadjust=0,yadjust=0):

        try:
            # Plotting pressure, temperature, and RPM throughout the run
            fig, ax1 = plt.subplots(figsize=(10,6))
            ax1.grid(linestyle='--', linewidth=1)
            ax2 = ax1.twinx()
            ax3 = ax1.twinx()
            ax4 = ax1.twinx()

            # Offsetting the axes so that they do not overlap
            ax3.spines["left"].set_position(("axes",-0.12))
            ax3.spines["left"].set_visible(True)
            ax3.yaxis.set_label_position('left')
            ax3.yaxis.set_ticks_position('left')

            ax4.spines["right"].set_position(("axes",1.12))

            ax1.plot([(x[2] - starttime)/3600000 for x in jmattributes[0]],[x[1] for x in jmattributes[0]],color='black',label = 'Spindle RPM')
            ax2.plot([(x[2] - starttime)/3600000 for x in jmattributes[1]],[x[1] for x in jmattributes[1]],color='red',label = 'Compressor Outlet Pressure')
            ax2.plot([(x[2] - starttime)/3600000 for x in jmattributes[2]],[x[1] for x in jmattributes[2]],color='green',label = 'Bottom Nozzle Pressure')
            ax3.plot([(x[2] - starttime)/3600000 for x in jmattributes[3]],[x[1] for x in jmattributes[3]],color='blue',label = 'Grinding Chamber Weight')
            ax4.plot([(x[2] - starttime)/3600000 for x in jmattributes[4]],[x[1] for x in jmattributes[4]],color='cyan',label = 'Grinding Chamber Temp')

            # Plotting empty arrays to ax2 just so that the legend will have everything
            ax2.plot([],[],color='black',label = 'Spindle RPM')
            ax2.plot([],[],color='blue',label = 'Grinding Chamber Weight')
            ax2.plot([],[],color='cyan',label = 'Grinding Chamber Temp')

            ax1.set_ylabel('RPM', fontsize=font_size)
            ax1.set_xlabel('Time Elapsed (Hours)',fontsize=font_size)
            ax2.set_ylabel('Pressure (mbar)', fontsize=font_size)
            ax3.set_ylabel('Weight (kg)', fontsize=font_size)
            ax4.set_ylabel('Temperature (C)', fontsize=font_size)

            legend = ax2.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1),
                    fancybox=True, shadow=True, ncol=3)

            plt.savefig(filepath + 'jmOverview.png',bbox_inches='tight')
            ax1.clear()
            ax2.clear()
            ax3.clear()
            ax4.clear()
            plt.cla()

            # Add plot to PDF
            sf.addPlot(pdf, 'Overview',filepath + 'jmOverview.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust)

        except:
            # Printing to the PDF that there was an error
            sf.writeHeader(pdf,'Overview',halfsize=halfsize)
            pdf.write(10, 'Unable to create Overview plot.\n\n')
            # Printing to the console
            print('Unable to create JM Overview plot.\n')


    ###############
    # Temperature #
    ###############

    def jmTemp(pdf,halfsize=False,xadjust=0,yadjust=0):

        try:
            # Plotting Temperature throughout the run
            fig, ax1 = plt.subplots(figsize=(10,6))
            ax1.grid(linestyle='--', linewidth=1)

            ax1.plot([(x[2] - starttime)/3600000 for x in jmattributes[5]],[x[1] for x in jmattributes[5]],label = 'Spindle Front Temp')
            ax1.plot([(x[2] - starttime)/3600000 for x in jmattributes[6]],[x[1] for x in jmattributes[6]],label = 'Spindle Rear Temp')
            ax1.plot([(x[2] - starttime)/3600000 for x in jmattributes[4]],[x[1] for x in jmattributes[4]],label = 'Grinding Chamber Temp')
            ax1.plot([(x[2] - starttime)/3600000 for x in jmattributes[7]],[x[1] for x in jmattributes[7]],label = 'Compressor Water Out Temp')
            ax1.plot([(x[2] - starttime)/3600000 for x in jmattributes[8]],[x[1] for x in jmattributes[8]],label = 'Heat Ex Out Temp')

            ax1.set_ylabel('Temperature (C)', fontsize=font_size)
            ax1.set_xlabel('Time Elapsed (Hours)',fontsize=font_size)

            legend = ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1),
                                fancybox=True, shadow=True, ncol=3)
            
            plt.savefig(filepath + 'jmTemp.png',bbox_inches='tight')
            ax1.clear()
            plt.cla()

            # Add plot to the PDF
            sf.addPlot(pdf, 'Temperature', filepath + 'jmTemp.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust)

        except:
            # Printing to the PDF that there was an error
            sf.writeHeader(pdf,'Temperature',halfsize=halfsize)
            pdf.write(10, 'Unable to create Temperature plot.\n\n')
            # Printing to the console
            print('Unable to create JM Temperature plot.\n')


    ########################
    # Oxygen and Dew Point #
    ########################

    def jmOxygen(pdf, halfsize=False, xadjust=0, yadjust=0):

        try:
            # Creating the figure
            fig, ax1 = plt.subplots(figsize=(10,6))
            ax1.grid(linestyle='--', linewidth=1)

            # Putting plots on the figure
            ax1.plot([(x[2] - starttime)/3600000 for x in jmattributes[9]],[x[1] for x in jmattributes[9]],label = 'Oxygen Sensor 1')
            ax1.plot([(x[2] - starttime)/3600000 for x in jmattributes[10]],[x[1] for x in jmattributes[10]],label = 'Oxygen Sensor 2')
            ax1.plot([(x[2] - starttime)/3600000 for x in jmattributes[11]],[x[1] for x in jmattributes[11]],label = 'Oxygen Sensor 3')
            ax1.plot([(x[2] - starttime)/3600000 for x in jmattributes[12]],[x[1] for x in jmattributes[12]],label = 'Dew Point')

            # Taking care of labeling
            ax1.set_xlabel('Time Elapsed (Hours)', fontsize=font_size)
            ax1.set_ylabel('PPM', fontsize=font_size)

            legend = ax1.legend(loc='upper center', bbox_to_anchor=(0.5,-0.1),
                                fancybox=True, shadow=True, ncol=3)
            
            # Saving figure and clearing everything
            plt.savefig(filepath + 'jmOxygen.png', bbox_inches='tight')
            ax1.clear()
            plt.cla()

            # Add plot to the PDF
            sf.addPlot(pdf, 'Oxygen and Dew Point', filepath + 'jmOxygen.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust)

        except:
            # Printing to the PDF that there was an error
            sf.writeHeader(pdf,'Oxygen and Dew Point',halfsize=halfsize)
            pdf.write(10, 'Unable to create Oxygen and Dew Point plot.\n\n')
            # Printing to the console
            print('Unable to create JM Oxygen and Dew Point plot.\n')


    ##############
    # Vibrations #
    ##############

    def jmVibrations(pdf, halfsize=False, xadjust=0, yadjust=0):

        try:
            # Creating the figure
            fig, ax1 = plt.subplots(figsize=(10,6))
            ax1.grid(linestyle='--', linewidth=1)

            # Putting plot on the figure
            ax1.plot([(x[2] - starttime)/3600000 for x in jmattributes[13]],[x[1] for x in jmattributes[13]],label = 'VS1303')
            ax1.plot([(x[2] - starttime)/3600000 for x in jmattributes[14]],[x[1] for x in jmattributes[14]],label = 'VS1304')
            ax1.plot([(x[2] - starttime)/3600000 for x in jmattributes[15]],[x[1] for x in jmattributes[15]],label = 'VS1305')
            
            ax1.set_xlabel('Time Elapsed (Hours)', fontsize=font_size)
            ax1.set_ylabel('Pressure (mbar)', fontsize=font_size)

            legend = ax1.legend(loc='upper center', bbox_to_anchor=(0.5,-0.1),
                                fancybox=True, shadow=True, ncol=3)
            
            # Saving figure and clearing everything
            plt.savefig(filepath + 'jmVibrations.png', bbox_inches='tight')
            ax1.clear()
            plt.cla()

            # Adding plot to the PDF
            sf.addPlot(pdf, 'Spindle Vibrations', filepath + 'jmVibrations.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust)

        except:
            # Printing to the PDF that there was an error
            sf.writeHeader(pdf,'Spindle Vibrations',halfsize=halfsize)
            pdf.write(10, 'Unable to create Spindle Vibrations plot.\n\n')
            # Printing to the console
            print('Unable to create JM Spindle Vibrations plot.\n')


    #############################
    # Jet Mill Power and Energy #
    #############################

    def jmPower(pdf, halfsize=False, xadjust=0, yadjust=0):

        try:
            # Creating the figure
            fig, ax1 = plt.subplots(figsize=(10,6))
            ax1.grid(linestyle='--', linewidth=1)
            ax2 = ax1.twinx()
            ax3 = ax1.twinx()

            # Offsetting the axes so that they do not overlap
            ax3.spines["right"].set_position(("axes",1.12))


            # Putting plot on the figure
            ax1.plot([(x[2] - starttime)/3600000 for x in jmattributes[16]],[x[1] for x in jmattributes[16]],color='blue',label = 'Total Active Power')
            ax2.plot([(x[2] - starttime)/3600000 for x in jmattributes[17]],[x[1] for x in jmattributes[17]],color='black',label = 'Total Apparent Power')
            ax3.plot([(x[2] - starttime)/3600000 for x in jmattributes[18]],[x[1] for x in jmattributes[18]],color='red',label = 'Total Active Energy Import')
            
            # Plotting empty arrays to ax1 just so that the legend will have everything
            ax1.plot([],[],color='black',label = 'Total Apparent Power')
            ax1.plot([],[],color='red',label = 'Total Active Energy Import')

            ax1.set_xlabel('Time Elapsed (Hours)', fontsize=font_size)
            ax1.set_ylabel('Power (kW)', fontsize=font_size)
            ax2.set_ylabel('Power (kVA)', fontsize=font_size)
            ax3.set_ylabel('Energy (kVAh)', fontsize=font_size)

            legend = ax1.legend(loc='upper center', bbox_to_anchor=(0.5,-0.1),
                                fancybox=True, shadow=True, ncol=3)
            
            # Saving figure and clearing everything
            plt.savefig(filepath + 'jmPower.png', bbox_inches='tight')
            ax1.clear()
            ax2.clear()
            ax3.clear()
            plt.cla()

            # Adding plot to the PDF
            sf.addPlot(pdf, 'Jet Mill Power | Energy Used: {} kVAh'.format(totalenergyjm), filepath + 'jmPower.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust)

        except:
            # Printing to the PDF that there was an error
            sf.writeHeader(pdf,'Jet Mill Power',halfsize=halfsize)
            pdf.write(10, 'Unable to create Jet Mill Power plot.\n\n')
            # Printing to the console
            print('Unable to create JM Jet Mill Power plot.\n')


    ###############################
    # Compressor Power and Energy #
    ###############################

    def jmCompressorPower(pdf, halfsize=False, xadjust=0, yadjust=0):

        try:
            # Creating the figure
            fig, ax1 = plt.subplots(figsize=(10,6))
            ax1.grid(linestyle='--', linewidth=1)
            ax2 = ax1.twinx()
            ax3 = ax1.twinx()

            # Offsetting the axes so that they do not overlap
            ax3.spines["right"].set_position(("axes",1.12))

            # Putting plot on the figure
            ax1.plot([(x[2] - starttime)/3600000 for x in jmattributes[19]],[x[1] for x in jmattributes[19]],color='blue',label = 'Total Active Power')
            ax2.plot([(x[2] - starttime)/3600000 for x in jmattributes[20]],[x[1] for x in jmattributes[20]],color='black',label = 'Total Apparent Power')
            ax3.plot([(x[2] - starttime)/3600000 for x in jmattributes[21]],[x[1] for x in jmattributes[21]],color='red',label = 'Total Active Energy Import')

            # Plotting empty arrays to ax1 just so that the legend will have everything
            ax1.plot([],[],color='black',label = 'Total Apparent Power')
            ax1.plot([],[],color='red',label = 'Total Active Energy Import')
            
            # Setting axis labels
            ax1.set_xlabel('Time Elapsed (Hours)', fontsize=font_size)
            ax1.set_ylabel('Power (kW)', fontsize=font_size)
            ax2.set_ylabel('Power (kVA)', fontsize=font_size)
            ax3.set_ylabel('Energy (kVAh)', fontsize=font_size)
            ax3.ticklabel_format(style='plain')

            legend = ax1.legend(loc='upper center', bbox_to_anchor=(0.5,-0.1),
                                fancybox=True, shadow=True, ncol=3)
            
            # Saving figure and clearing everything
            plt.savefig(filepath +'jmCompressorPower.png', bbox_inches='tight')
            ax1.clear()
            ax2.clear()
            ax3.clear()
            plt.cla()

            # Adding plot to the PDF
            sf.addPlot(pdf, 'Compressor Power | Energy Used: {} kVAh'.format(totalenergycomp), filepath + 'jmCompressorPower.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust)

        except:
            # Printing to the PDF that there was an error
            sf.writeHeader(pdf,'Compressor Power',halfsize=halfsize)
            pdf.write(10, 'Unable to create Compressor Power plot.\n\n')
            # Printing to the console
            print('Unable to create JM Compressor Power plot.\n')


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
            ax1.plot([(x[2] - starttime)/3600000 for x in jmattributes[22]],[x[1] for x in jmattributes[22]],color='blue',label = 'Temperature')
            ax2.plot([(x[2] - starttime)/3600000 for x in jmattributes[23]],[x[1] for x in jmattributes[23]],color='black',label = 'Relative Humidity')
            ax3.plot([(x[2] - starttime)/3600000 for x in jmattributes[24]],[x[1] for x in jmattributes[24]],color='red',label = 'Barometric Pressure')

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
            pdf.cell(40, 6, datetime.datetime.fromtimestamp(jmattributes[22][0][2]/1000).strftime('%Y-%m-%d %H:%M:%S'), 1, 0, 'C')
            pdf.cell(40, 6, str(round(jmattributes[22][0][1],2)), 1, 0, 'C')
            pdf.cell(40, 6, str(round(jmattributes[23][0][1],2)), 1, 0, 'C')
            pdf.cell(40, 6, str(round(jmattributes[24][0][1],2)), 1, 1, 'C')

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
            ax1.plot([(x[2] - starttime)/3600000 for x in jmattributes[25]],[x[1] for x in jmattributes[25]],color='blue',label = 'Temperature')
            ax2.plot([(x[2] - starttime)/3600000 for x in jmattributes[26]],[x[1] for x in jmattributes[26]],color='black',label = 'Relative Humidity')

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
            pdf.cell(40, 6, datetime.datetime.fromtimestamp(jmattributes[25][0][2]/1000).strftime('%Y-%m-%d %H:%M:%S'), 1, 0, 'C')
            pdf.cell(40, 6, str(round(jmattributes[25][0][1],2)), 1, 0, 'C')
            pdf.cell(40, 6, str(round(jmattributes[26][0][1],2)), 1, 1, 'C')

            # Adding plot to the PDF
            sf.addPlot(pdf, 'Indoor Weather Station', filepath + 'indoorWeather.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust, header=False)

        except:
            # Printing to the PDF that there was an error
            pdf.write(10, 'Unable to create Indoor Weather Station plot.\n\n')
            # Printing to the console
            print('Unable to create Indoor Weather Station plot.\n')


    ###################################
    # Particle Size Distribution Plot #
    ###################################

    def psaDistribution(pdf, halfsize=False, xadjust=0, yadjust=0):

        # Only create a plot if there is data for the run, and the data isn't a list full of zeros
        if len(psaMeasurements[0]) > 0 and [float(x[2]) for x in psaMeasurements[0]] != [float(0) for x in psaMeasurements[0]]:
            try:
                # Creating the figure
                fig, ax1 = plt.subplots(figsize=(10,6))
                ax1.grid(linestyle='--', linewidth=1)
                plt.xscale("log")
                # Setting the x axis limit to 100
                plt.xlim(0.1,100)
                ax2 = ax1.twinx()

                # Putting plots on the figure
                # Currently, plots are only made for a measurement ID of 1. Some runs have multiple measurements though
                ax1.plot([x[2] for x in psaMeasurements[0]],[x[4] for x in psaMeasurements[0]], color='black', label='Cumulative Volume', marker='D')
                ax2.plot([x[2] for x in psaMeasurements[0]],[x[3] for x in psaMeasurements[0]], color='blue', label = 'Volume Frequency', marker='D')

                # Plotting empty arrays to ax1 just so that the legend will have everything
                ax1.plot([],[],color='blue',label = 'Volume Frequency')

                # Setting axis labels
                ax1.set_xlabel('Particle Diameter (um)', fontsize=font_size)
                ax1.set_ylabel('Cumulative Volume (%)', fontsize=font_size)
                ax2.set_ylabel('Volume Frequency (%)',fontsize=font_size)

                legend = ax1.legend(loc='upper center', bbox_to_anchor=(0.5,-0.1),
                                    fancybox=True, shadow=True, ncol=2)

                # Saving figure and clearing everything
                plt.savefig(filepath + 'psaDistribution.png', bbox_inches='tight')
                ax1.clear()
                ax2.clear()
                plt.cla()

                print('PSA Run Info:')
                print(psaRunInfo)

                # Adding plot to the PDF
                sf.addPlot(pdf, 'Particle Size Distribution: Sample Number: {}, Measurement Number: {}'.format(psaRunInfo[0][2], psaMeasurements[0][0][1]), filepath + 'psaDistribution.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust)
            
            except:
                # Printing to the PDF that there was an error
                sf.writeHeader(pdf,'Particle Size Distribution',halfsize=halfsize)
                pdf.write(10, 'Unable to create Particle Size Distribution plot.\n\n')
                # Printing to the console
                print('Unable to create Particle Size Distribution plot.\n')


    ##################################
    # Particle Size Analysis Section #
    ##################################

    def psa(pdf):

        # Adding in a section for run settings for each of the PSA runs
        for i in range(len(psaMeasurements)):
            print(i)
            if len(psaMeasurements[i]) > 0 and [float(x[2]) for x in psaMeasurements[i]] != [float(0) for x in psaMeasurements[i]]:

                print('PSA Run Info:')
                print(psaRunInfo[0][2])

                # Particle Size Analysis Section
                pdf.add_page()
                sf.writeHeader(pdf,'Particle Size Analysis: Sample Number: {}, Measurement Number: {}'.format(psaRunInfo[0][2], psaMeasurements[0][0][1]))
                # Subsection containing all of the PSA run settings
                # If this section is at the top of the page, add a little extra room between the two headers
                if pdf.get_y() < 40:
                    pdf.ln(10)
                sf.writeHeader(pdf, 'Run Settings', halfsize=True)

                # Writing in all of the run settings
                offset = 0
                pdf.ln(5)
                top = pdf.get_y()

                # Writing the run settings if they are able to be found
                try:
                    for k in range(len(runsettingsheader)):
                        value = psaSettings[i][0][k+2]
                        pdf.set_font('Helvetica','b',10)
                        pdf.multi_cell(35,4.5,runsettingsheader[k])
                        pdf.set_xy(35 + offset + pdf.l_margin, pdf.get_y()-4.5)
                        pdf.set_font('Helvetica','',10)
                        pdf.multi_cell(45,4.5,value)
                        pdf.set_x(offset + pdf.l_margin)

                        if k == 7:
                            offset = 75
                            pdf.set_xy(offset + pdf.l_margin, top)
                # If the run settings are not found, print that they are not found
                except:
                    pdf.write(10, 'Unable to find run settings.\n\n')

                # Subsection containing PSA standard values
                sf.writeHeader(pdf, 'Standard Values', halfsize=True)

                # Writing in all of the standard values
                offset = 0
                pdf.ln(5)
                top = pdf.get_y()
                # Writing the standard values if they are able to be found
                try:
                    for k in range(len(runstandardsheader)):
                        value = psaRunStandards[i][0][k+3]
                        pdf.set_font('Helvetica','b',10)
                        pdf.multi_cell(35,4.5,runstandardsheader[k])
                        pdf.set_xy(35 + offset + pdf.l_margin, pdf.get_y()-4.5)
                        pdf.set_font('Helvetica','',10)
                        pdf.multi_cell(35,4.5,str(value))
                        pdf.set_x(offset + pdf.l_margin)

                        if k == 4:
                            offset = 75
                            pdf.set_xy(offset + pdf.l_margin, top)
                # If the standard values are not found, print that they are not found
                except:
                    pdf.write(10, 'Unable to find standard values.\n\n')

                # Adding in the plot of particle size distributions
                psaDistribution(pdf)


    ##########################
    # Printing batch details #
    ##########################
    
    def batchDetails(pdf):

        # Writing in the batch details
        pdf.set_font('Helvetica', '', 10)
        pdf.multi_cell(55,5.5,'Batch ID')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(85,5.5,runarray[0][3])
        pdf.multi_cell(55,5.5,'Product ID')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(85,5.5,str(runarray[0][4]) + ' (' + sf.productType(runarray[0][4]) + ')')
        pdf.multi_cell(55,5.5,'Output Quantity (Dashboard)')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(85,5.5,runarray[0][5][0])
        pdf.multi_cell(55,5.5,'Output Quantity (Transfer Bottles)')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(85,5.5,runarray[0][5][1])
        pdf.multi_cell(55,5.5,'Operator ID')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(85,5.5,runarray[0][8])
        pdf.multi_cell(55,5.5,'Description')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(135,5.5,runarray[0][7])
        pdf.multi_cell(55,5.5,'Equipment')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(105,5.5,runarray[0][9] + ' (ID: ' + runarray[0][2] + ')')
        pdf.multi_cell(55,5.5,'Date')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(105,5.5,str(runarray[0][6]))
        pdf.multi_cell(55,5.5,'Total Run Time')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(85,5.5,str(totalruntime))
        pdf.multi_cell(55,5.5,'Total Energy Consumption \n(Jet Mill + Compressor)')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-11.0)
        pdf.multi_cell(85,11.0,str(totalenergyjm + totalenergycomp) + ' kVAh')
        pdf.multi_cell(55,5.5,'Multiplier Applied?')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        if multiply == True:
            pdf.multi_cell(85,5.5,'Yes')
        else:
            pdf.multi_cell(85,5.5,'No')


    # Create a singular report
    def addSingular(pdf):

        # Creating a new title page
        pdf.add_page()
        pdf.set_font('Helvetica', 'b', 16)
        pdf.ln(5)
        pdf.write(5, 'Jet Mill Report')
        pdf.ln(8)

        # Adding in the batch details
        batchDetails(pdf)

        # Transfer bottle information
        sf.transferBottles(batchid=batchid, pdf=pdf)

        # Adding in the plots
        jmOverview(pdf)
        jmTemp(pdf)
        jmOxygen(pdf)
        jmVibrations(pdf)
        jmPower(pdf)
        jmCompressorPower(pdf)

        # Adding in the PSA section
        psa(pdf)

        # Adding in the run parameters
        sf.runParameters(pdf, runarray[1])

        # Adding in the list of tag IDs that were used to gather data
        sf.addTags(jmattributes_tagids, pdf=pdf)

        # Closing all figures so that they don't stay open and take up too much memory if function is called multiple times
        plt.close('all')


    # Function that adds all new sections to comprehensive report
    def addComprehensive(pdf):

        # Creating a new page and header for each report added to this bigger report
        pdf.add_page()
        pdf.set_font('Helvetica', 'b', 16)  
        pdf.ln(5)
        pdf.write(5, 'Process ' + str(runarray[0][0]) + ' - ' + str(runarray[0][1]))
        pdf.ln(8)

        # Adding in the batch details
        batchDetails(pdf)

        # Transfer bottle information
        sf.transferBottles(batchid=batchid, pdf=pdf)

        # Adding in the recipe parameters
        recipeParameters(recipeid=runinfo[0][5])

        # Adding in the plots
        ybefore = pdf.get_y()
        jmOverview(pdf=pdf, halfsize=True)

        if ybefore < 200:
            pdf.set_y(ybefore)
        else:
            pdf.set_y(10)

        jmTemp(pdf=pdf, halfsize=True, xadjust=90)

        ybefore = pdf.get_y()
        jmOxygen(pdf=pdf, halfsize=True)

        if ybefore < 200:
            pdf.set_y(ybefore)
        else:
            pdf.set_y(10)

        jmVibrations(pdf=pdf, halfsize=True, xadjust=90)

        ybefore=pdf.get_y()
        jmPower(pdf=pdf, halfsize=True)

        if ybefore < 200:
            pdf.set_y(ybefore)
        else:
            pdf.set_y(10)

        jmCompressorPower(pdf=pdf, halfsize=True, xadjust=90)

        pdf.add_page()
        indoorWeatherStation(pdf=pdf, halfsize=True)
        outdoorWeatherStation(pdf=pdf, halfsize=True)

        # Particle Size Analysis Section
        psa(pdf)

        # Adding in the run parameters
        sf.runParameters(pdf, runarray[1])

        # Adding in the list of tag IDs that were used to gather data
        sf.addTags(jmattributes_tagids, pdf=pdf)

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


    # Adding sections to the report based on what the reporttype is
    if reporttype == 'comprehensive':
        addComprehensive(pdf)
    elif reporttype == 'singular':
        addSingular(pdf)
    elif reporttype == 'customer':
        addCustomer(pdf)