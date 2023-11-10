# This script is to create reports based on outgassing runs

#################################
# Importing Necessary Libraries #
#################################

import spareFunctions as sf
import datetime
import matplotlib.pyplot as plt
import numpy as np
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

ogattributes_tagids = [{"name":"Average Temperature", "tagid":"8146"},
                    {"name":"Internal Temperature", "tagid":"7484"},
                    {"name":"Pressure", "tagid":"7139"},
                    {"name":"MOT1007", "tagid":"7753"},
                    {"name":"MOT1003", "tagid":"7736"},
                    {"name":"FT1021", "tagid":"7535"},
                    {"name":"FT1021 Setpoint", "tagid":"7537"},
                    {"name":"PID1017 Setpoint", "tagid":"7799"},
                    {"name":"TT1016", "tagid":"7471"},
                    {"name":"TT1017", "tagid":"7472"},
                    {"name":"TT1018", "tagid":"7473"},
                    {"name":"TT1022", "tagid":"7484"},
                    {"name":"PT1034", "tagid":"7734"},
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

    # Specifying batch ID
    batchid = runarray[0][3]

    # Getting run information where the batch ID matches
    cur.execute("SELECT id, equipment_id, batch_id, product_id, employee_id, comment, timestamp FROM equipment_runs WHERE batch_id='{}'".format(batchid))
    runinfo = sf.makeArray(cur.fetchall())[0]

    print(runinfo)

    print('\nStarting time is: {}'.format(runinfo[6]))

    # Determining what date the batch was run in, in the format of YYYY-MM-DD
    day = runinfo[6].strftime("%Y-%m-%d")
    month = day[5:7]
    year = day[0:4]

    # If the day is before the cutoff date, then change the database name to the appropriate year
    if runinfo[6].strftime("%Y-%m-%d") <= cutoffdate:
        database = 'SCADA_' + year
    else:
        database = 'SCADA_' + year + '_' + month
        
    # Getting a starting table from the date in runinfo
    starttable = database + '.sqlt_data_1_' + datetime.datetime.strftime(runinfo[6], "%Y%m%d")
    tables = [starttable]

    # Creating a timestamp from the datetime listed in the hd run table eq_hds
    starttime = int(datetime.datetime.timestamp(runinfo[6])*1000)

    # Adding 3 hours to the starttime, and calling it the stoptime
    stoptime = starttime + 3600000*3

    print('Stop time is: {}\n'.format(datetime.datetime.fromtimestamp(stoptime/1000)))

    totalruntime = datetime.datetime.fromtimestamp(stoptime/1000) - datetime.datetime.fromtimestamp(starttime/1000)


    # Now get data from SCADA database between start and stop times
    ogattributes = []
    for element in ogattributes_tagids:

        # First changing the tag ID to include all related tag IDs to account for any being retired
        element["tagid"] = sf.getAllTags(element["tagid"])

        subarray = []

        for table in tables:
            cur.execute("SELECT tagid, intvalue, floatvalue, stringvalue, datevalue, t_stamp FROM {} WHERE tagid IN ({}) AND t_stamp > {} AND t_stamp < {} ORDER BY t_stamp ASC".format(table,element["tagid"],starttime,stoptime))
            array = sf.makeArray(cur.fetchall(),removeNone=True)
            subarray = subarray + array

        obscure(subarray)
        ogattributes.append(subarray)



    ##################
    # Creating plots #
    ##################

    # Setting a font size to be used in all the graphs for uniformity
    font_size=12

    # Vessel temperature, pressure
    def ogTemp(pdf,halfsize=False, xadjust=0,yadjust=0):

        try:
            # Plotting pressure, temperature, and RPM throughout the run
            fig, ax1 = plt.subplots(figsize=(10,6))
            ax1.grid(linestyle='--', linewidth=1)
            ax2 = ax1.twinx()
            ax3 = ax1.twinx()

            # Offsetting the axes so that they do not overlap
            ax3.spines["right"].set_position(("axes",1.12))

            ax1.plot([(x[2] - starttime)/3600000 for x in ogattributes[0]],[x[1] for x in ogattributes[0]],color='black',label = 'Average Temperature')
            ax1.plot([(x[2] - starttime)/3600000 for x in ogattributes[1]],[x[1] for x in ogattributes[1]],color='red',label = 'Internal Temperature')
            ax2.plot([(x[2] - starttime)/3600000 for x in ogattributes[2]],[x[1] for x in ogattributes[2]],color='green',label = 'Pressure')
            ax3.plot([(x[2] - starttime)/3600000 for x in ogattributes[3]],[x[1] for x in ogattributes[3]],color='blue',label = 'MOT1007')
            ax3.plot([(x[2] - starttime)/3600000 for x in ogattributes[4]],[x[1] for x in ogattributes[4]],color='cyan',label = 'MOT1003')

            # Plotting empty arrays to ax1 just so that the legend will have everything
            ax1.plot([],[],color='green',label = 'Pressure')
            ax1.plot([],[],color='blue',label = 'MOT1007')
            ax1.plot([],[],color='cyan',label = 'MOT1003')

            ax1.set_ylabel('Temp (C)', fontsize=font_size)
            ax1.set_xlabel('Time Elapsed (Hours)',fontsize=font_size)
            ax2.set_ylabel('Pressure (mbar)', fontsize=font_size)
            ax3.set_ylabel('RPM', fontsize=font_size)

            start, end = ax1.get_ylim()
            ax1.yaxis.set_ticks(np.arange(0, end, 100))

            legend = ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1),
                    fancybox=True, shadow=True, ncol=3)

            plt.savefig(filepath + 'ogTemperature.png',bbox_inches='tight')
            ax1.clear()
            ax2.clear()
            ax3.clear()
            plt.cla()

            # Add plot to PDF
            sf.addPlot(pdf, 'OG Temperature, Pressure, RPM',filepath + 'ogTemperature.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust)

        except:
            # Printing to the PDF that there was an error
            sf.writeHeader(pdf,'OG Temperature, Pressure, RPM',halfsize=halfsize)
            pdf.write(10, 'Unable to create OG Temperature, Pressure, RPM plot.\n\n')
            # Printing to the console
            print('Unable to create OG Temperature, Pressure, RPM plot.\n')


    # Argon Flow
    def ogArgonFlow(pdf,halfsize=False,xadjust=0,yadjust=0):

        try:
            # Plotting Argon flow throughout the run
            fig, ax1 = plt.subplots(figsize=(10,6))
            ax1.grid(linestyle='--', linewidth=1)

            ax1.plot([(x[2] - starttime)/3600000 for x in ogattributes[5]],[x[1] for x in ogattributes[5]],label = 'FT1021 PV')
            ax1.plot([(x[2] - starttime)/3600000 for x in ogattributes[6]],[x[1] for x in ogattributes[6]],label = 'FT1021 SP')

            ax1.set_ylabel('Flow (l/min)', fontsize=font_size)
            ax1.set_xlabel('Time Elapsed (Hours)',fontsize=font_size)

            legend = ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1),
                                fancybox=True, shadow=True, ncol=2)
            
            plt.savefig(filepath + 'ogArgonFlow.png',bbox_inches='tight')
            ax1.clear()
            plt.cla()

            # Add plot to the PDF
            sf.addPlot(pdf, 'Argon Flow', filepath + 'ogArgonFlow.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust)

        except:
            # Printing to the PDF that there was an error
            sf.writeHeader(pdf,'Argon Flow',halfsize=halfsize)
            pdf.write(10, 'Unable to create Argon Flow plot.\n\n')
            # Printing to the console
            print('Unable to create Argon Flow plot.\n')

    # Furnace Actual Temperature
    def ogFurnaceTemp(pdf, halfsize=False, xadjust=0, yadjust=0):

        try:
            # Creating the figure
            fig, ax1 = plt.subplots(figsize=(10,6))
            ax1.grid(linestyle='--', linewidth=1)

            # Putting plots on the figure
            ax1.plot([(x[2] - starttime)/3600000 for x in ogattributes[7]],[x[1] for x in ogattributes[7]],label = 'PID 1017 SP')
            ax1.plot([(x[2] - starttime)/3600000 for x in ogattributes[8]],[x[1] for x in ogattributes[8]],label = 'TT1016')
            ax1.plot([(x[2] - starttime)/3600000 for x in ogattributes[9]],[x[1] for x in ogattributes[9]],label = 'TT1017')
            ax1.plot([(x[2] - starttime)/3600000 for x in ogattributes[10]],[x[1] for x in ogattributes[10]],label = 'TT1018')
            ax1.plot([(x[2] - starttime)/3600000 for x in ogattributes[11]],[x[1] for x in ogattributes[11]],label = 'TT1022')

            # Taking care of labeling
            ax1.set_xlabel('Time Elapsed (Hours)', fontsize=font_size)
            ax1.set_ylabel('Temperature (C)', fontsize=font_size)

            legend = ax1.legend(loc='upper center', bbox_to_anchor=(0.5,-0.1),
                                fancybox=True, shadow=True, ncol=5)
            
            # Saving figure and clearing everything
            plt.savefig(filepath + 'ogFurnaceTemp.png', bbox_inches='tight')
            ax1.clear()
            plt.cla()

            # Add plot to the PDF
            sf.addPlot(pdf, 'Furnace Actual Temperature', filepath + 'ogFurnaceTemp.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust)

        except:
            # Printing to the PDF that there was an error
            sf.writeHeader(pdf,'Furnace Actual Temperature',halfsize=halfsize)
            pdf.write(10, 'Unable to create Furnace Actual Temperature plot.\n\n')
            # Printing to the console
            print('Unable to create Furnace Actual Temperature plot.\n')


    # Furnace Pressure
    def ogPressure(pdf, halfsize=False, xadjust=0, yadjust=0):

        try:
            # Creating the figure
            fig, ax1 = plt.subplots(figsize=(10,6))
            ax1.grid(linestyle='--', linewidth=1)

            # Putting plot on the figure
            ax1.plot([(x[2] - starttime)/3600000 for x in ogattributes[12]],[x[1] for x in ogattributes[12]],label = 'PT1034')
            
            ax1.set_xlabel('Time Elapsed (Hours)', fontsize=font_size)
            ax1.set_ylabel('Pressure (mbar)', fontsize=font_size)

            legend = ax1.legend(loc='upper center', bbox_to_anchor=(0.5,-0.1),
                                fancybox=True, shadow=True, ncol=1)
            
            # Saving figure and clearing everything
            plt.savefig(filepath + 'ogPressure.png', bbox_inches='tight')
            ax1.clear()
            plt.cla()

            # Adding plot to the PDF
            sf.addPlot(pdf, 'Furnace Pressure', filepath + 'ogPressure.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust)

        except:
            # Printing to the PDF that there was an error
            sf.writeHeader(pdf,'Furnace Pressure',halfsize=halfsize)
            pdf.write(10, 'Unable to create Furnace Pressure plot.\n\n')
            # Printing to the console
            print('Unable to create Furnace Pressure plot.\n')


    # Outdoor Weather Station
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
            ax1.plot([(x[2] - starttime)/3600000 for x in ogattributes[13]],[x[1] for x in ogattributes[13]],color='blue',label = 'Temperature')
            ax2.plot([(x[2] - starttime)/3600000 for x in ogattributes[14]],[x[1] for x in ogattributes[14]],color='black',label = 'Relative Humidity')
            ax3.plot([(x[2] - starttime)/3600000 for x in ogattributes[15]],[x[1] for x in ogattributes[15]],color='red',label = 'Barometric Pressure')

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
            pdf.cell(40, 6, datetime.datetime.fromtimestamp(ogattributes[13][0][2]/1000).strftime('%Y-%m-%d %H:%M:%S'), 1, 0, 'C')
            pdf.cell(40, 6, str(round(ogattributes[13][0][1],2)), 1, 0, 'C')
            pdf.cell(40, 6, str(round(ogattributes[14][0][1],2)), 1, 0, 'C')
            pdf.cell(40, 6, str(round(ogattributes[15][0][1],2)), 1, 1, 'C')

            # Adding plot to the PDF
            sf.addPlot(pdf, 'Outdoor Weather Station', filepath + 'outdoorWeather.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust, header=False)

        except:
            # Printing to the PDF that there was an error
            pdf.write(10, 'Unable to create Outdoor Weather Station plot.\n\n')
            # Printing to the console
            print('Unable to create Outdoor Weather Station plot.\n')

    # Indoor Weather Station
    def indoorWeatherStation(pdf, halfsize=False, xadjust=0, yadjust=0):

        try:
            # Creating the figure
            fig, ax1 = plt.subplots(figsize=(10,6))
            ax1.grid(linestyle='--', linewidth=1)
            ax2 = ax1.twinx()

            # Putting plot on the figure
            ax1.plot([(x[2] - starttime)/3600000 for x in ogattributes[16]],[x[1] for x in ogattributes[16]],color='blue',label = 'Temperature')
            ax2.plot([(x[2] - starttime)/3600000 for x in ogattributes[17]],[x[1] for x in ogattributes[17]],color='black',label = 'Relative Humidity')

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
            pdf.cell(40, 6, datetime.datetime.fromtimestamp(ogattributes[16][0][2]/1000).strftime('%Y-%m-%d %H:%M:%S'), 1, 0, 'C')
            pdf.cell(40, 6, str(round(ogattributes[16][0][1],2)), 1, 0, 'C')
            pdf.cell(40, 6, str(round(ogattributes[17][0][1],2)), 1, 1, 'C')

            # Adding plot to the PDF
            sf.addPlot(pdf, 'Indoor Weather Station', filepath + 'indoorWeather.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust, header=False)

        except:
            # Printing to the PDF that there was an error
            pdf.write(10, 'Unable to create Indoor Weather Station plot.\n\n')
            # Printing to the console
            print('Unable to create Indoor Weather Station plot.\n')


    # Printing batch details
    def batchDetails(pdf):

        # Writing in the batch details
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
        pdf.multi_cell(55,5.5,'Multiplier Applied?')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        if multiply == True:
            pdf.multi_cell(85,5.5,'Yes')
        else:
            pdf.multi_cell(85,5.5,'No')


    #################################
    # Adding sections to the report #
    #################################

    # Adding sections to the PDF for single report
    def addSingular(pdf):
        # Creating a title page
        pdf.add_page()
        pdf.set_font('Helvetica', 'b', 16)
        pdf.ln(5)
        pdf.write(5, 'Outgassing Report')
        pdf.ln(8)

        # Writing in the batch details
        batchDetails(pdf)

        # Transfer bottle information
        sf.transferBottles(batchid=batchid, pdf=pdf)

        # Adding the plots to the PDF
        ogTemp(pdf)
        ogArgonFlow(pdf)
        ogFurnaceTemp(pdf)
        ogPressure(pdf)

        # Adding in the list of tag IDs that were used to gather data
        sf.addTags(ogattributes_tagids, pdf=pdf)

        # Closing all figures so that they don't stay open and take up too much memory if function is called multiple times
        plt.close('all')


    # Adding the sections to the PDF for comprehensive report
    def addComprehensive(pdf):

        # Creating a new page and header for each report added to this bigger report
        pdf.add_page()
        pdf.set_font('Helvetica', 'b', 16)  
        pdf.ln(5)
        pdf.write(5, 'Process ' + str(runarray[0][0]) + ' - ' + str(runarray[0][1]))
        pdf.ln(8)

        # Writing in the batch details
        batchDetails(pdf)

        # Transfer bottle information
        sf.transferBottles(batchid=batchid, pdf=pdf)
        pdf.add_page()

        # Adding the plots to the PDF
        if pdf.get_y() > 200:
            pdf.add_page()
            
        ybefore = pdf.get_y()
        ogTemp(pdf=pdf, halfsize=True)

        if ybefore > 200:
            pdf.set_y(10)
        else:
            pdf.set_y(ybefore)

        ogArgonFlow(pdf=pdf, halfsize=True, xadjust=90)

        ybefore = pdf.get_y()
        ogFurnaceTemp(pdf=pdf, halfsize=True)

        if ybefore < 200:
            pdf.set_y(ybefore)
        else:
            pdf.add_page()
            pdf.set_y(10)

        ogPressure(pdf=pdf, halfsize=True, xadjust=90)

        pdf.add_page()
        indoorWeatherStation(pdf=pdf, halfsize=True)
        outdoorWeatherStation(pdf=pdf, halfsize=True)

        # Adding in the list of tag IDs that were used to gather data
        sf.addTags(ogattributes_tagids, pdf=pdf)

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


    # Add sections to the report based on whether it calls for singular or comprehensive
    if reporttype == 'singular':
        addSingular(pdf=pdf)
    elif reporttype == 'comprehensive':
        addComprehensive(pdf=pdf)
    elif reporttype == 'customer':
        addCustomer(pdf)