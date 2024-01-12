# This script is to create reports based on sieving runs

#################################
# Importing Necessary Libraries #
#################################

import spareFunctions as sf
import datetime
import matplotlib.pyplot as plt
import numpy as np
import secrets
from matplotlib.ticker import MultipleLocator


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

attributes_tagids = [{"name":"Weather Station Temp", "tagid":"17230"},
                    {"name":"Weather Station RH", "tagid":"17229"},
                    {"name":"Weather Station Pressure", "tagid":"17226"},
                    {"name":"HD Platform Temp", "tagid":"24399"},
                    {"name":"HD Platform RH", "tagid":"24397"}]

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

    # Finding the starting time of the run by finding the TB with the earliest time, and subtracting an hour from it
    cur.execute("SELECT time_filled FROM eq_transfer_bottles_status WHERE batch_id='{}' ORDER BY time_filled ASC LIMIT 1".format(batchid))
    try:
        startdatetime = cur.fetchall()[0][0] - datetime.timedelta(hours=1)
    except:
        startdatetime = runarray[0][6] - datetime.timedelta(hours=1)

    print('Starting time is: {}'.format(startdatetime))


    # Changing to match the new database name
    database = 'SCADA_History'
        
    # Getting a starting table from the date in runinfo
    starttable = database + '.sqlt_data_1_' + datetime.datetime.strftime(startdatetime, "%Y%m%d")
    tables = [starttable]

    # Creating a timestamp from the datetime listed in the hd run table eq_hds
    starttime = int(datetime.datetime.timestamp(startdatetime)*1000)

    # Adding 1 hour to the starttime, and calling it the stoptime
    stoptime = starttime + 3600000

    print('Stop time is: {}'.format(datetime.datetime.fromtimestamp(stoptime/1000)))

    totalruntime = datetime.datetime.fromtimestamp(stoptime/1000) - datetime.datetime.fromtimestamp(starttime/1000)


    ##########################
    # Attributes Information #
    ##########################

    attributes = []
    for element in attributes_tagids:

        # Getting all tag IDs that are associated with the current element
        tagids = sf.getAllTags(element["tagid"])

        subarray = []
        for table in tables:

            cur.execute("SELECT tagid, intvalue, floatvalue, stringvalue, datevalue, t_stamp FROM {} WHERE tagid IN ({}) AND t_stamp BETWEEN {} AND {} ORDER BY t_stamp ASC".format(table,tagids,starttime,stoptime))
            array = sf.makeArray(cur.fetchall(),removeNone=True)
            subarray = subarray + array

        attributes.append(subarray)


    ####################
    # Weather Stations #
    ####################

    # Setting a font size for all y axis labels, and distance between ticks and gridlines on x axis
    font_size = 16
    xticks = 3
    minorLocator = MultipleLocator(1)

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
            ax1.plot([(x[2] - starttime)/3600000 for x in attributes[0]],[x[1] for x in attributes[0]],color='blue',label = 'Temperature')
            ax2.plot([(x[2] - starttime)/3600000 for x in attributes[1]],[x[1] for x in attributes[1]],color='black',label = 'Relative Humidity')
            ax3.plot([(x[2] - starttime)/3600000 for x in attributes[2]],[x[1] for x in attributes[2]],color='red',label = 'Barometric Pressure')

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
            pdf.cell(40, 6, datetime.datetime.fromtimestamp(attributes[0][0][2]/1000).strftime('%Y-%m-%d %H:%M:%S'), 1, 0, 'C')
            pdf.cell(40, 6, str(round(attributes[0][0][1],2)), 1, 0, 'C')
            pdf.cell(40, 6, str(round(attributes[1][0][1],2)), 1, 0, 'C')
            pdf.cell(40, 6, str(round(attributes[2][0][1],2)), 1, 1, 'C')

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
            ax1.plot([(x[2] - starttime)/3600000 for x in attributes[3]],[x[1] for x in attributes[3]],color='blue',label = 'Temperature')
            ax2.plot([(x[2] - starttime)/3600000 for x in attributes[4]],[x[1] for x in attributes[4]],color='black',label = 'Relative Humidity')

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
            pdf.cell(40, 6, datetime.datetime.fromtimestamp(attributes[3][0][2]/1000).strftime('%Y-%m-%d %H:%M:%S'), 1, 0, 'C')
            pdf.cell(40, 6, str(round(attributes[3][0][1],2)), 1, 0, 'C')
            pdf.cell(40, 6, str(round(attributes[4][0][1],2)), 1, 1, 'C')

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
        pdf.multi_cell(55,5.5,'Output Quantity (HMI)')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-6.5)
        pdf.multi_cell(85,5.5,runarray[0][5][2])
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

        # Weather station information
        indoorWeatherStation(pdf=pdf, halfsize=True)
        outdoorWeatherStation(pdf=pdf, halfsize=True)

        # Adding in the list of tag IDs that were used to gather data
        sf.addTags(attributes_tagids, pdf=pdf)

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

        indoorWeatherStation(pdf=pdf, halfsize=True)
        outdoorWeatherStation(pdf=pdf, halfsize=True)

        # Adding in the list of tag IDs that were used to gather data
        sf.addTags(attributes_tagids, pdf=pdf)

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


