# This is a version of sfCreateReport that is modular with the purpose of being able to create different
# reports depending on what the user requests. 


#################################
# Importing Necessary Libraries #
#################################

import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import datetime
import numpy as np
from bisect import bisect_left
import spareFunctions as sf
import secrets
from fpdf import FPDF
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
import sys


# Creating a PDF class with a footer that has the page numbers
class PDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, 'Page ' + str(self.page_no()), 0, 0, 'C')
pdf = PDF()


def makeReport(batchid, runarray, filepath, multiply=False, reporttype='full',pdf=pdf,iteration=''):

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

        # Create the new multiplied array by multiplying each element of the original array by the multiplier
        multipliedarray = [(array[k]*multiplier) for k in range(len(array))]
        return multipliedarray


    #######################################
    # Establishing connection to database #
    #######################################

    # Connection to SCADA database
    cur = sf.cur
    # Connection to UMCDB
    umccur = sf.umccur

    # Creating a cutoff date for when database names change format
    cutoffdate = '2021-12-31'

    # Tagids for temp measurements, pressure, etc.
    attributes_tagids_sf1 = [{"name":"Pressure", "tagid":"27745"},   #1002
                            {"name":"Vacuum", "tagid":"27716"},     #975
                            {"name":"Active Power", "tagid":"6497"}, #3960
                            {"name":"Apparent Power", "tagid":"6505"}, #3972
                            {"name":"Active Energy Import", "tagid":"6465"}, # 6465, 4267  _panel_ehd3_/sinteringfurnace1/4_meter43204-4_meter43204/4_meter43204
                            {"name":"Cooling RPM", "tagid":"1079"},
                            {"name":"Weather Station Temp", "tagid":"17230"},
                            {"name":"Weather Station RH", "tagid":"17229"},
                            {"name":"Weather Station Pressure", "tagid":"17226"},
                            {"name":"HD Platform Temp", "tagid":"24399"},
                            {"name":"HD Platform RH", "tagid":"24397"},
                            {"name":"Furnace TC", "tagid":"27761"}]
    
    # # Tagids for temp measurements, pressure, etc.
    # attributes_tagids_sf1 = [{"name":"Pressure", "tagid":"27745"},   #1002
    #                         {"name":"Vacuum", "tagid":"27716"},     #975
    #                         {"name":"Active Power", "tagid":"6497"}, #3960
    #                         {"name":"Apparent Power", "tagid":"6505"}, #3972
    #                         {"name":"Active Energy Import", "tagid":"6465"}, # 6465, 4267  _panel_ehd3_/sinteringfurnace1/4_meter43204-4_meter43204/4_meter43204
    #                         {"name":"Front Temperature", "tagid":"1840"},
    #                         {"name":"Center Temperature", "tagid":"1839"},
    #                         {"name":"Rear Temperature", "tagid":"1843"},
    #                         {"name":"P1", "tagid":"1833"},
    #                         {"name":"P2", "tagid":"1834"},
    #                         {"name":"P3", "tagid":"1835"},
    #                         {"name":"P4", "tagid":"1836"},
    #                         {"name":"P5", "tagid":"1837"},
    #                         {"name":"P6", "tagid":"1838"},
    #                         {"name":"P7", "tagid":"1845"},
    #                         {"name":"P8", "tagid":"1847"},
    #                         {"name":"P9", "tagid":"1848"},
    #                         {"name":"P10", "tagid":"1849"},
    #                         {"name":"P11", "tagid":"1850"},
    #                         {"name":"P12", "tagid":"1846"},
    #                         {"name":"P13", "tagid":"1841"},
    #                         {"name":"P14", "tagid":"1842"},
    #                         {"name":"P15", "tagid":"1844"},
    #                         {"name":"Cooling RPM", "tagid":"1079"},
    #                         {"name":"Weather Station Temp", "tagid":"17230"},
    #                         {"name":"Weather Station RH", "tagid":"17229"},
    #                         {"name":"Weather Station Pressure", "tagid":"17226"},
    #                         {"name":"HD Platform Temp", "tagid":"24399"},
    #                         {"name":"HD Platform RH", "tagid":"24397"},
    #                         {"name":"Furnace TC", "tagid":"27761"}]
    
    attributes_tagids_sf2 = [{"name":"Pressure", "tagid":"3322"},
                            {"name":"Vacuum", "tagid":"25917"},
                            {"name":"Active Power", "tagid":"6606"},
                            {"name":"Apparent Power", "tagid":"6604"},
                            {"name":"Active Energy Import", "tagid":"6601"},
                            {"name":"Cooling RPM", "tagid":"25866"},
                            {"name":"Weather Station Temp", "tagid":"17230"},
                            {"name":"Weather Station RH", "tagid":"17229"},
                            {"name":"Weather Station Pressure", "tagid":"17226"},
                            {"name":"HD Platform Temp", "tagid":"24399"},
                            {"name":"HD Platform RH", "tagid":"24397"},
                            {"name":"Furnace TC", "tagid":"25853"}] #3320
    
    attributes_tagids_sf3 = [{"name":"Pressure", "tagid":"29597"},
                            {"name":"Vacuum", "tagid":"29615"},
                            {"name":"Active Power", "tagid":"10386"},
                            {"name":"Apparent Power", "tagid":"10388"},      
                            {"name":"Active Energy Import", "tagid":"10391"},
                            {"name":"Cooling RPM", "tagid":"29593"},
                            {"name":"Weather Station Temp", "tagid":"17230"},
                            {"name":"Weather Station RH", "tagid":"17229"},
                            {"name":"Weather Station Pressure", "tagid":"17226"},
                            {"name":"HD Platform Temp", "tagid":"24399"},
                            {"name":"HD Platform RH", "tagid":"24397"},
                            {"name":"Furnace TC", "tagid":"29566"}]
    
    attributes_tagids_sf4 = [{"name":"Pressure", "tagid":"2824"},
                            {"name":"Vacuum", "tagid":"2821"},
                            {"name":"Active Power", "tagid":"6606"},        # Incorrect tag ID
                            {"name":"Apparent Power", "tagid":"6604"},      # Incorrect tag ID
                            {"name":"Active Energy Import", "tagid":"6601"},    # Incorrect tag ID
                            {"name":"Cooling RPM", "tagid":"2817"},
                            {"name":"Weather Station Temp", "tagid":"17230"},
                            {"name":"Weather Station RH", "tagid":"17229"},
                            {"name":"Weather Station Pressure", "tagid":"17226"},
                            {"name":"HD Platform Temp", "tagid":"24399"},
                            {"name":"HD Platform RH", "tagid":"24397"},
                            {"name":"Furnace TC", "tagid":"2825"}]

    # Tagids for temperature probes
    probe_tagids = [{"name":"P1", "tagid":"1833"},
                    {"name":"P2", "tagid":"1834"},
                    {"name":"P3", "tagid":"1835"},
                    {"name":"P4", "tagid":"1836"},
                    {"name":"P5", "tagid":"1837"},
                    {"name":"P6", "tagid":"1838"},
                    {"name":"P7", "tagid":"1845"},
                    {"name":"P8", "tagid":"1847"},
                    {"name":"P9", "tagid":"1848"},
                    {"name":"P10", "tagid":"1849"},
                    {"name":"P11", "tagid":"1850"},
                    {"name":"P12", "tagid":"1846"},
                    {"name":"P13", "tagid":"1841"},
                    {"name":"P14", "tagid":"1842"},
                    {"name":"P15", "tagid":"1844"},
                    {"name":"P16", "tagid":"1840"},
                    {"name":"P17", "tagid":"1839"},
                    {"name":"P18", "tagid":"1843"}]


    ###########################
    # Current run information #
    ###########################

    # Finding the starting timestamp from the input batch using SCADA.equipment_runs
    cur.execute("SELECT id, equipment_id, batch_id, product_id, employee_id, recipe_id, comment, timestamp FROM equipment_runs WHERE batch_id='{}' ORDER BY timestamp DESC".format(batchid))
    runinfo = sf.makeArray(cur.fetchall())

    # If the batch number corresponds to multiple entries in the table, then print a message saying so, and use the first entry
    if len(runinfo) > 1:
        print('Multiple entries in SCADA.equipment_runs for batch ID {}. The most recent run will be used'.format(batchid))
    
    runinfo = runinfo[0]

    
    try:
        # Getting quantity
        cur.execute("SELECT weight, weight_type FROM equipment_run_weights WHERE equipment_run_id='{}'".format(runinfo[0]))
        results = sf.makeArray(cur.fetchall())[0]
        for element in results:
            runinfo.append(element)
            if reporttype == 'comprehensive' or reporttype == 'customer':
                runarray[0][5].append(element)
            else:
                runarray[5].append(element)
    except:
        runinfo = runinfo + ['Missing'] * 2
        if reporttype == 'comprehensive' or reporttype == 'customer':
            runarray[0][5].append('Missing')
        else:
            runarray[5].append('Missing')

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
    year = day[0:4]
    month = day[5:7]

    # If the day is on or before the cutoff date, then change the database name to the appropriate name
    if day <= cutoffdate:
        database = 'SCADA_' + year
    else:
        database = 'SCADA_' + year + '_' + month

    # Changing to match the new database name
    # database = 'SCADA_History'

    # Generating name of the first table to be looked at, based off of timestamp associated with batch ID input
    # If the start time is before 7:47 AM, then the table will be the previous day's table. Otherwise it is the same day's table
    if runinfo[7].hour < 7 or (runinfo[7].hour == 7 and runinfo[7].minute < 47):
        starttable = database + '.sqlt_data_1_' + (runinfo[7] - datetime.timedelta(days=1)).strftime("%Y%m%d")
        nexttable = database + '.sqlt_data_1_' + runinfo[7].strftime("%Y%m%d")
        tables = [starttable, nexttable]
    else:
        starttable = database + '.sqlt_data_1_' + runinfo[7].strftime("%Y%m%d")
        tables = [starttable]
    currentday = runinfo[7]

    # Determining the correct on/off tag for the equipment, and correct set of tags
    equipment_id = runinfo[1]
    if equipment_id == 2:
        onoff = sf.getAllTags(27104) #5872
        attributes_tagids = attributes_tagids_sf1
    elif equipment_id == 3:
        onoff = sf.getAllTags(26106) #6044
        attributes_tagids = attributes_tagids_sf2
    elif equipment_id == 4:
        onoff = sf.getAllTags(29825)
        attributes_tagids = attributes_tagids_sf3
    elif equipment_id == 5:
        onoff = sf.getAllTags(6048)
        attributes_tagids = attributes_tagids_sf4
    else:
        print('There are no attribute tag IDs for this equipment ID ({})'.format(equipment_id))


    ################################
    # Finding start and stop times #
    ################################

    # Getting tag 5872 data from start table(s)
    onoffdata = []
    for table in tables:
        print(table)
        cur.execute("SELECT intvalue, t_stamp FROM {} WHERE tagid IN ({})".format(table,onoff))
        onoffdata += sf.makeArray(cur.fetchall())

    # Now determining where the start point of the run is
    startpoint = [i for i in range(1,len(onoffdata)) if onoffdata[i-1][0] == 0 and onoffdata[i][0] == 1]
    print('Initial startpoints: {}'.format(startpoint))
    initialstarttimes = [datetime.datetime.fromtimestamp(onoffdata[i][1]/1000) for i in startpoint]
    print('Initial starttimes: {}'.format(initialstarttimes))


    # If there are multiple startpoints, then use the one whose index corresponds closest to the date listed in runinfo[7]
    if len(startpoint) > 1:
        timedifferences = []

        for point in startpoint:

            # Finding the time that corresponds to that startpoint
            time = onoffdata[point][1]

            # Calculating the time difference between that point and the runinfo[7] date
            timediff = abs(time - runinfo[7].timestamp()*1000)

            # As long as the endpoint does not occur within an hour after the startpoint, then add the point to the list of time differences
            endpoint = [i for i in range(point,len(onoffdata) - 1) if onoffdata[i][0] == 1 and onoffdata[i+1][0] == 0]
            if len(endpoint) > 0:
                if endpoint[-1] - point > 720:
                    timedifferences.append([point,timediff])

            # If there is no endpoint, then add the point to the list of time differences
            else:
                timedifferences.append([point,timediff])

        # Sorting the list of time differences by the time difference
        timedifferences.sort(key=lambda x: x[1])

        # The startpoint is the point that corresponds to the smallest time difference
        if len(timedifferences) > 0:
            startpoint = [timedifferences[0][0]]
        else:
            startpoint = []

    # If the endpoint is less than an hour after the startpoint, then that run will not be looked at
    if len(startpoint) > 0:
        endpoint = [i for i in range(startpoint[-1],len(onoffdata) - 1) if onoffdata[i][0] == 1 and onoffdata[i+1][0] == 0]
        if len(endpoint) > 0:
            if endpoint[-1] - startpoint[-1] < 720:
                startpoint = []

    # If the startpoint was not in the table, then get the previous table and check for the startpoint in there
    
    while startpoint == []:

        # Getting the previous day
        previousday = currentday - datetime.timedelta(days=1)
        year = previousday.strftime('%Y')
        month = previousday.strftime('%m')

        # If the previous day is before the cutoff date, then change the database name to the appropriate year
        if previousday.strftime("%Y-%m-%d") <= cutoffdate:
            database = 'SCADA_' + year
        else:
            database = 'SCADA_' + year + '_' + month

        # Finding the table associated with the previous day
        previoustable = database + '.sqlt_data_1_' + previousday.strftime('%Y%m%d')
        tables = [previoustable]

        # Getting tag 5872 data from previous table
        cur.execute("SELECT intvalue, t_stamp FROM {} WHERE tagid IN ({})".format(previoustable,onoff))
        previousonoffdata = sf.makeArray(cur.fetchall())

        onoffdata = previousonoffdata

        # Now determining where the start point of the run is
        startpoint = [i for i in range(1,len(onoffdata)) if onoffdata[i-1][0] == 0 and onoffdata[i][0] == 1]

        # If the endpoint is less than an hour after the startpoint, then continue going back to look for another run
        if len(startpoint) > 0:
            endpoint = [i for i in range(startpoint[-1],len(onoffdata) - 1) if onoffdata[i][0] == 1 and onoffdata[i+1][0] == 0]
            if len(endpoint) > 0:
                if endpoint[-1] - startpoint[-1] < 720:
                    startpoint = []
        currentday = previousday


    # Now determining where the end point of the run is
    endpoint = [i for i in range(startpoint[-1],len(onoffdata)-1) if onoffdata[i][0] == 1 and onoffdata[i+1][0] == 0]

    # If the endpoint was not in the table, then get the next table and check for the endpoint in there
    while endpoint == []:

        print('The endpoint for batch ID {} was not in the table. Looking in the next table...'.format(batchid))

        # Getting the next day
        nextday = currentday + datetime.timedelta(days=1)
        year = nextday.strftime('%Y')
        month = nextday.strftime('%m')

        # If the next day is before the cutoff date, then change the database name to the appropriate year
        if nextday.strftime("%Y-%m-%d") <= cutoffdate:
            database = 'SCADA_' + year
        else:
            database = 'SCADA_' + year + '_' + month

        # Finding the table associated with the next day
        nexttable = database + '.sqlt_data_1_' + nextday.strftime('%Y%m%d')
        tables.append(nexttable)

        # Getting tag 5872 data from next table
        cur.execute("SELECT intvalue, t_stamp FROM {} WHERE tagid IN ({})".format(nexttable,onoff))
        endingonoffdata = sf.makeArray(cur.fetchall())
        onoffdata = onoffdata + endingonoffdata
        
        # Now determining where the end point of the run is
        endpoint = [i for i in range(startpoint[-1],len(onoffdata)-1) if onoffdata[i][0] == 1 and onoffdata[i+1][0] == 0]

        # Since the endpoint is being searched for in the next table, use the first endpoint that comes up
        if len(endpoint) > 0:
            endpoint = [endpoint[0]]
        
        currentday = nextday


    # Determining exact start and stop timestamps
    # In case there are multiple runs on the same day (test runs etc) Make the start point be the very first of the day, and end point is the very last? Might change
    starttime = onoffdata[startpoint[-1]][1]
    stoptime = onoffdata[endpoint[0]][1]


    # Looking at the furnace temperature at the stoptime. If the temperature is above 75, then the stoptime will be the point when the temperature drops below 75
    # Getting the furnace temperature data from the tables
    try:
        cur.execute("SELECT intvalue, t_stamp FROM {} WHERE tagid IN ({}) AND t_stamp < {} ORDER BY t_stamp DESC LIMIT 1".format(tables[-1],sf.getAllTags(attributes_tagids[11]['tagid']),stoptime))
        result = sf.makeArray(cur.fetchall())[0]
        furnace_temp = result[0]
    except:
        furnace_temp = 76

    # If the furnace temperature is above 75, then find the point when the temperature drops below 75
    while furnace_temp > 75:

        print('\n\n\nFurnace temperature is above 75 C at the end of the run. Looking for the point when the temperature drops below 75...')

        # Getting the first furnace temperature that is under 75 and past the stoptime
        cur.execute("SELECT intvalue, t_stamp FROM {} WHERE tagid IN ({}) AND t_stamp > {} AND intvalue < {} ORDER BY t_stamp ASC LIMIT 1".format(tables[-1],sf.getAllTags(attributes_tagids[11]['tagid']),stoptime,75))

        try:
            result = sf.makeArray(cur.fetchall())[0]
            furnace_temp = result[0]
            stoptime = result[1]
            print('New stoptime: {}'.format(datetime.datetime.fromtimestamp(stoptime/1000)))
        except:
            print('All furnace temps in this table after the stoptime are above 75. Will check the next table')

        # If the furnace temperature is still above 75, then add the next table to the list of tables
        if furnace_temp > 75:
            nextday = currentday + datetime.timedelta(days=1)
            year = nextday.strftime('%Y')
            month = nextday.strftime('%m')

            # If the next day is before the cutoff date, then change the database name to the appropriate year
            if nextday.strftime("%Y-%m-%d") <= cutoffdate:
                database = 'SCADA_' + year
            else:
                database = 'SCADA_' + year + '_' + month

            # Finding the table associated with the next day
            nexttable = database + '.sqlt_data_1_' + nextday.strftime('%Y%m%d')
            tables.append(nexttable)
            currentday = nextday


    # Printing the current run's start and stop times
    print('\nCurrent run start time: {}'.format(datetime.datetime.fromtimestamp(starttime/1000)))
    print('Current run end time: {}'.format(datetime.datetime.fromtimestamp(stoptime/1000)))
    print('\n')


    # Determining when the previous run took place, so parameters can be compared
    # Begin by attempting to find a start and end point in the beginning table
    prevendpoint = [i for i in range(startpoint[0]) if onoffdata[i][0] == 1 and onoffdata[i+1][0] == 0]
    prevstartpoint = [i for i in range(1,startpoint[0]-2) if onoffdata[i-1][0] == 0 and onoffdata[i][0] == 1]

    # Determining whether or not the end point is in the start table or not. If not, that table will be removed from previousruntables
    previousruntables = [starttable]
    prevonoffdata = []
    for table in previousruntables:
        cur.execute("SELECT intvalue, t_stamp FROM {} WHERE tagid IN ({}) AND t_stamp < {}".format(table,onoff,starttime))
        prevonoffdata = sf.makeArray(cur.fetchall())

    prevendpoint = [i for i in range(len(prevonoffdata) - 1) if prevonoffdata[i][0] == 1 and prevonoffdata[i + 1][0] == 0]

    # If the previous endpoint is not contained within the startday table, then remove that table from the list of tables
    if prevendpoint == []:
        previousruntables = []

    # Finding the startpoint of the previous run, if it does not occur in the start table
    j = 1
    while prevstartpoint == []:
        
        # Getting the previous day
        previousday = currentday - datetime.timedelta(days=j)
        year = previousday.strftime('%Y')
        month = previousday.strftime('%m')

        # If the previous day is before the cutoff date, then change the database name to the appropriate year
        if previousday.strftime("%Y-%m-%d") <= cutoffdate:
            database = 'SCADA_' + year
        else:
            database = 'SCADA_' + year + '_' + month

        # Finding the table associated with the previous day
        previoustable = database + '.sqlt_data_1_' + previousday.strftime('%Y%m%d')
        previousruntables.insert(0,previoustable)

        # Get tag 5872 data from tables
        # The list prevtag5872 needs to be rewritten every time a new table is added so that things can stay in chronological order
        prevonoffdata = []
        for table in previousruntables:
            cur.execute("SELECT intvalue, t_stamp FROM {} WHERE tagid IN ({}) AND t_stamp < {}".format(table,onoff,starttime))
            array = sf.makeArray(cur.fetchall())
            prevonoffdata = prevonoffdata + array

        prevstartpoint = [i for i in range(1,len(prevonoffdata) - 1) if prevonoffdata[i-1][0] == 0 and prevonoffdata[i][0] == 1]
        prevendpoint = [i for i in range(len(prevonoffdata) - 1) if prevonoffdata[i][0] == 1 and prevonoffdata[i + 1][0] == 0]

        # If the endpoint is not contained within the tables being checked, then remove those tables (Except for the last)
        if prevendpoint == []:
            previousruntables = [previoustable]
        
        j = j + 1

    prevendpoint = [i for i in range(prevstartpoint[0],len(prevonoffdata) - 1) if prevonoffdata[i][0] == 1 and prevonoffdata[i + 1][0] == 0]

    # Exact start and stop timestamps of the previous run
    # If the batch is B230368 then set the previous start and stop times to the start and stop times described above for B230367
    if batchid == 'B230368':
        previousstarttime = 1697978689000
        previousstoptime = 1698021813000
    else:
        previousstarttime = prevonoffdata[prevstartpoint[0]][1]
        previousstoptime = prevonoffdata[prevendpoint[0]][1]

    # Determining the total run time
    totalruntime = datetime.datetime.fromtimestamp(stoptime/1000) - datetime.datetime.fromtimestamp(starttime/1000)

    # Printing the previous run times
    print('Previous run start time: {}'.format(datetime.datetime.fromtimestamp(previousstarttime/1000)))
    print('Previous run end time: {}'.format(datetime.datetime.fromtimestamp(previousstoptime/1000)))
    print('\n')


    #################################################
    # Getting list of tags to be used in parameters #
    #################################################

    def getParameterValues():

        # Creating list of tag definitions so each tag's identity is known
        cur.execute("SELECT id, name, unit, param_type, tag_id FROM equipment_params WHERE equipment_id = {}".format(equipment_id))
        tagdefs = sf.makeArray(cur.fetchall())

        # Finding the equipment_run_id and batch_id of the previous run
        # Note, batch ID of previous run for this equipment is not necessarily the component batch ID!
        cur.execute("SELECT id, batch_id, recipe_id FROM equipment_runs WHERE equipment_id = {} AND id < {} ORDER BY id DESC LIMIT 1".format(equipment_id,runinfo[0]))
        results = cur.fetchall()
        previousrunid = results[0][0]
        previousrunbatchid = results[0][1]
        previousrecipeid = results[0][2]


        ############
        # Method 1 #
        ############

        # Getting run parameters from equipment_run_values table
        furnaceparameters = []
        for tag in tagdefs:
            cur.execute("SELECT intvalue, floatvalue, stringvalue, datevalue FROM equipment_run_values WHERE equipment_run_id = {} AND param_id = {}".format(runinfo[0],tag[0]))
            try:
                array = sf.makeArray(cur.fetchall(),removeNone=True)[0]
            except:
                array = []
            array.insert(0,tag[4])
            array.insert(1,tag[1])
            if len(array) > 2:
                furnaceparameters.append(array)

        # Getting previous run parameters from equipment_run_values table
        previousparameters = []
        for tag in tagdefs:
            cur.execute("SELECT intvalue, floatvalue, stringvalue, datevalue FROM equipment_run_values WHERE equipment_run_id = {} AND param_id = {}".format(previousrunid,tag[0]))
            try:
                array = sf.makeArray(cur.fetchall(),removeNone=True)[0]
            except:
                array = []
            array.insert(0,tag[4])
            array.insert(1,tag[1])
            if len(array) > 2:
                previousparameters.append(array)


        ############
        # Method 2 #
        ############

        # If no parameter values were found for the current run, then try to get parameters from recipe_id if runinfo[5] is not null
        if len(furnaceparameters) == 0 and runinfo[5] != None:
            print('\nNo parameter values found in equipment_run_values table for {}. \nSearching through equipment_recipe_values instead'.format(batchid))
            cur.execute("SELECT param_id, intvalue, floatvalue, stringvalue, datevalue FROM equipment_recipe_values WHERE recipe_id = {}".format(runinfo[5]))
            recipevalues = sf.makeArray(cur.fetchall(),removeNone=True)

            # Combining recipe values with the tag definitions
            furnaceparameters = []
            if len(recipevalues) > 0:
                for tag in tagdefs:
                    for element in recipevalues:
                        if tag[0] == element[0]:
                            array = [tag[4],tag[1],element[1]]
                            furnaceparameters.append(array)

        # If no parameter values were found for the previous run, then try to get parameters from recipe_id if previousrecipeid is not null
        if len(previousparameters) == 0 and previousrecipeid != None:
            print('\nNo parameter values found in equipment_run_values table for previous run. \nSearching through equipment_recipe_values instead')

            cur.execute("SELECT param_id, intvalue, floatvalue, stringvalue, datevalue FROM equipment_recipe_values WHERE recipe_id = {}".format(previousrecipeid))
            recipevalues = sf.makeArray(cur.fetchall(),removeNone=True)

            # Combining recipe values with the tag definitions
            previousparameters = []
            if len(recipevalues) > 0:
                for tag in tagdefs:
                    for element in recipevalues:
                        if tag[0] == element[0]:
                            array = [tag[4],tag[1],element[1]]
                            previousparameters.append(array)


        # If the parameter values have been found, then print that they were found
        if len(furnaceparameters) > 0:
            print('\nCurrent run parameter values have been found')
        else:
            print('\nCurrent run parameter values have not been found. \nSearching through sqlt_data_1_YYYYMMDD table instead')

        if len(previousparameters) > 0:
            print('\nPrevious run parameter values have been found')
        else:
            print('\nPrevious run parameter values have not been found. \nSearching through sqlt_data_1_YYYYMMDD table instead')


        ############
        # Method 3 #
        ############

        # If no parameter values were found for the current run, then try searching through the sqlt_data_1_YYYYMMDD table
        if len(furnaceparameters) == 0:
            # Gathering parameter information from right after the beginning of the run
            furnaceparameters = []
            for tag in tagdefs:
                cur.execute("SELECT intvalue, floatvalue, stringvalue, datevalue \
                    FROM {} WHERE tagid={} \
                    AND t_stamp BETWEEN {} AND {} ORDER BY t_stamp ASC LIMIT 1".format(tables[0],tag[4],starttime,stoptime))
                results = cur.fetchall()
                try:
                    array = sf.makeArray(results,removeNone=True)[0]
                except:
                    array = []

                array.insert(0,tag[0])
                array.insert(1,tag[1])

                if len(array) > 2:
                    furnaceparameters.append(array)

        # If no parameter values were found for the previous run, then try searching through the sqlt_data_1_YYYYMMDD table
        if len(previousparameters) == 0:

            # Creating table name where previous run parameters will be gathered from
            prevparamtable = database + '.sqlt_data_1_' + datetime.datetime.fromtimestamp(previousstarttime/1000).strftime('%Y%m%d')

            # Now need to gather parameter information from previous run
            previousparameters = []
            for tag in tagdefs:
                cur.execute("SELECT intvalue, floatvalue, stringvalue, datevalue \
                    FROM {} WHERE tagid={} \
                    AND t_stamp BETWEEN {} AND {} ORDER BY t_stamp DESC LIMIT 1".format(prevparamtable,tag[4],previousstarttime,previousstoptime))
                try:
                    array = sf.makeArray(cur.fetchall(),removeNone=True)[0]
                except:
                    array = []

                array.insert(0,tag[0])
                array.insert(1,tag[1])

                if len(array) > 2:
                    previousparameters.append(array)

        
        ############
        # Method 4 #
        ############

        # If no parameter values were found for the current run, then try searching through the eq_sintering_furnaces_parameters table
        if len(furnaceparameters) == 0:
            cur.execute("SELECT id FROM eq_sintering_furnaces WHERE batch_id = '{}'".format(batchid))
            eqsfid = cur.fetchall()[0][0]

            # Getting parameter information from eq_sintering_furnaces_parameters table
            furnaceparameters = []
            for tag in tagdefs:
                cur.execute("SELECT intvalue, floatvalue, stringvalue, datevalue FROM eq_sintering_furnaces_parameters WHERE sintering_furnaces_id = {} AND tagid = {}".format(eqsfid, tag[4]))
                try:
                    array = sf.makeArray(cur.fetchall(),removeNone=True)[0]
                except:
                    array = []
                array.insert(0,tag[4])
                array.insert(1,tag[1])
                if len(array) > 2:
                    furnaceparameters.append(array)

        # If no parameter values were found for the previous run, then try searching through the eq_sintering_furnaces_parameters table
        if len(previousparameters) == 0:

            # Getting previous run parameters from eq_sintering_furnaces_parameters table
            cur.execute("SELECT id FROM eq_sintering_furnaces WHERE batch_id = '{}'".format(previousrunbatchid))
            preveqsfid = cur.fetchall()[0][0]

            # Getting parameter information from eq_sintering_furnaces_parameters table
            previousparameters = []
            for tag in tagdefs:
                cur.execute("SELECT intvalue, floatvalue, stringvalue, datevalue FROM eq_sintering_furnaces_parameters WHERE sintering_furnaces_id = {} AND tagid = {}".format(preveqsfid, tag[4]))
                try:
                    array = sf.makeArray(cur.fetchall(),removeNone=True)[0]
                except:
                    array = []
                array.insert(0,tag[4])
                array.insert(1,tag[1])
                if len(array) > 2:
                    previousparameters.append(array)


        ############
        # Method 5 #
        ############

        # If no parameter values were found for the current run, then try searching through the eq_sintering_furnaces_tag_definitions table
        if len(furnaceparameters) == 0:
            print('\nNo parameter values found using newest tag IDs for current run. \nSearching through eq_sintering_furnaces_tag_definitions for older tag IDs to use instead')

            # Getting tag definitions from eq_sintering_furnaces_tag_definitions table
            cur.execute("SELECT tagid, definition FROM eq_sintering_furnaces_tag_definitions")
            tagdefs = sf.makeArray(cur.fetchall())

            # Using each of these tag definitions to find the parameter values from the sqlt_data_1_YYYYMMDD table
            furnaceparameters = []
            for tag in tagdefs:
                cur.execute("SELECT intvalue, floatvalue, stringvalue, datevalue \
                    FROM {} WHERE tagid={} \
                    AND t_stamp BETWEEN {} AND {} ORDER BY t_stamp ASC LIMIT 1".format(tables[0],tag[0],starttime,stoptime))
                results = cur.fetchall()
                try:
                    array = sf.makeArray(results,removeNone=True)[0]
                except:
                    array = []

                array.insert(0,tag[0])
                array.insert(1,tag[1])

                if len(array) > 2:
                    furnaceparameters.append(array)

        # If no parameter values were found for the previous run, then try searching through the eq_sintering_furnaces_tag_definitions table
        if len(previousparameters) == 0:

            print('\nNo parameter values found using newest tag IDs for previous run. \nSearching through eq_sintering_furnaces_tag_definitions for older tag IDs to use instead')

            # Getting tag definitions from eq_sintering_furnaces_tag_definitions table
            cur.execute("SELECT tagid, definition FROM eq_sintering_furnaces_tag_definitions")
            tagdefs = sf.makeArray(cur.fetchall())

            # Using each of these tag definitions to find the parameter values from the sqlt_data_1_YYYYMMDD table
            previousparameters = []
            for tag in tagdefs:
                cur.execute("SELECT intvalue, floatvalue, stringvalue, datevalue \
                    FROM {} WHERE tagid={} \
                    AND t_stamp BETWEEN {} AND {} ORDER BY t_stamp DESC LIMIT 1".format(prevparamtable,tag[0],previousstarttime,previousstoptime))
                try:
                    array = sf.makeArray(cur.fetchall(),removeNone=True)[0]
                except:
                    array = []

                array.insert(0,tag[0])
                array.insert(1,tag[1])

                if len(array) > 2:
                    previousparameters.append(array)

        
        # If parameter values still have not been found, then print that they have not been found
        if len(furnaceparameters) == 0:
            print('\nCurrent run parameter values have not been found. \nNo parameter values will be used in the report and will likely cause issues')
        if len(previousparameters) == 0:
            print('\nPrevious run parameter values have not been found. \nNo parameter values will be used in the report and will likely cause issues')


        # Iterating through the list of current and previous tag definitions, and combining them into one list
        for element in furnaceparameters:
            for item in previousparameters:
                if element[0] == item[0]:
                    element.append(item[2])

        # This is the format of each element of furnaceparameters:
        # [tagid, name, current value, previous value]


        # Creating a list with just time and temperature setpoints, and another with just setpoint tag IDs
        setpointlist = []
        setpointtags =[]

        # Heating cycle setpoint 1 temperature/time setting
        # Iterating through the list of furnace parameters, and finding the temperature and time setpoints
        for k in range(30):
            for element in furnaceparameters:
                if element[1] == 'Heating cycle setpoint {} temperature setting'.format(k+1) or element[1] == 'Step{}_Temp'.format(k+1):
                    # Appending the current and previous temperature setpoints to the setpointlist, with step number
                    setpointlist.append(['Step ' + str(k + 1),element[2],element[3]])
                    # Appending the tag ID to the setpoint tags list, with step number
                    setpointtags.append(['Step ' + str(k + 1),element[0]])

        # Iterating through the list again, and finding the time settings
        for k in range(30):
            for element in furnaceparameters:
                if element[1] == 'Heating cycle setpoint {} time setting'.format(k+1) or element[1] == 'Step{}_Time'.format(k+1):
                    # Inserting the current and previous time setpoints into the setpointlist
                    setpointlist[k].insert(2,element[2])
                    setpointlist[k].insert(4,element[3])
                    # Appending the time tag ID to the setpoint tags list
                    setpointtags[k].append(element[0])

        # Inserting an initial "step 0" to the setpointlist as a starting point
        setpointlist.insert(0,['Step 0',20,0,20,0])

        # Creating a setpoint list that only contains as many setpoints as there are in the current run
        currentsetpointlist = []
        for element in setpointlist:
            if element[1] != 0:
                currentsetpointlist.append(element)

        # Removing all elements in furnaceparameters that contain setpoint information (Contain the phrase Heating cycle setpoint or Step)
        furnaceparameters = [x for x in furnaceparameters if 'Heating cycle setpoint' not in x[1]]
        furnaceparameters = [x for x in furnaceparameters if 'Step' not in x[1]]

        # Modifying the parameter values (other than the already modified setpoint temp values) to be obscured
        for k in range(len(furnaceparameters)):
            multiplier = multipliers[secrets.randbelow(5)]
            newvalue = [furnaceparameters[k][0],furnaceparameters[k][1],furnaceparameters[k][2]*multiplier,furnaceparameters[k][3]*multiplier]
            furnaceparameters[k] = newvalue
        
        return furnaceparameters, setpointlist, setpointtags, currentsetpointlist


    ##################################
    # Getting Information for Graphs #
    ##################################

    # Getting the necessary data for full or comprehensive reports
    if reporttype == 'full' or reporttype == 'comprehensive' or reporttype == 'single':

        # Getting parameter values
        global parametervalues
        global setpointlist
        global setpointtags
        global currentsetpointlist
        parametervalues, setpointlist, setpointtags, currentsetpointlist = getParameterValues()

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

        # Creating arrays for specific attributes and their times
        # All of these arrays will be going into plots
        maxlength = len(attributes[1]) - 12 # Creating a maxlength variable, which will be used to shorten the lists of data to the same length
        coolingrpm = obscure([(x[1]*0.98333) for x in attributes[5][:maxlength]])
        coolingrpmtimeselapsed = [(x[2] - starttime)/3600000 for x in attributes[5][:maxlength]]
        pressure = obscure([x[1] for x in attributes[0][:maxlength]])
        vacuum = obscure([x[1] for x in attributes[1][:maxlength]])
        activepower = obscure([x[1] for x in attributes[2][:maxlength]])
        apparentpower = obscure([x[1] for x in attributes[3][:maxlength]])
        energyimport = obscure([x[1] for x in attributes[4][:maxlength]])
        # tempsf = obscure([x[1] for x in attributes[5][:maxlength]],type='temperature')
        # tempsc = obscure([x[1] for x in attributes[6][:maxlength]],type='temperature')
        # tempsr = obscure([x[1] for x in attributes[7][:maxlength]],type='temperature')
        pressuretime = [(x[2] - starttime)/3600000 for x in attributes[0][:maxlength]]
        vacuumtime = [(x[2] - starttime)/3600000 for x in attributes[1][:maxlength]]
        activepowertime = [(x[2] - starttime)/3600000 for x in attributes[2][:maxlength]]
        apparentpowertime = [(x[2] - starttime)/3600000 for x in attributes[3][:maxlength]]
        energyimporttime = [(x[2] - starttime)/3600000 for x in attributes[4][:maxlength]]
        # tempsftimes = [datetime.datetime.fromtimestamp(x[2]/1000) for x in attributes[5][:maxlength]]
        # tempsftimeselapsed = [(x[2] - starttime)/3600000 for x in attributes[5][:maxlength]]
        # tempsctimeselapsed = [(x[2] - starttime)/3600000 for x in attributes[6][:maxlength]]
        # tempsrtimeselapsed = [(x[2] - starttime)/3600000 for x in attributes[7][:maxlength]]
        blockdeltatimeselapsed = [(x[2] - starttime)/3600000 for x in attributes[11][:maxlength]]
        furnacetemperature = obscure([x[1] for x in attributes[11][:maxlength]],type='temperature')
        furnacetemperaturetime = [(x[2] - starttime)/3600000 for x in attributes[11][:maxlength]]
        furnacetcactualtime = [datetime.datetime.fromtimestamp(x[2]/1000) for x in attributes[11][:maxlength]]

        # Creating arrays of setpoint times and temperatures, and then obscuring them
        settimes,settemps = sf.expandSetpoints(currentsetpointlist,templocation=1,timelocation=2)

    # Getting the necessary information for the customer reports
    elif reporttype == 'customer':
        attributes = []

        # Getting a list of tagids associated with the Active Energy Import attribute tag
        tagids = sf.getAllTags(attributes_tagids[4]["tagid"])

        # Getting the Active Energy Import data
        subarray = []
        for table in tables:
            cur.execute("SELECT tagid, intvalue, floatvalue, stringvalue, datevalue, t_stamp FROM {} WHERE tagid IN ({}) AND t_stamp BETWEEN {} AND {} ORDER BY t_stamp ASC".format(table,tagids,starttime,stoptime))
            array = sf.makeArray(cur.fetchall(), removeNone=True)
            subarray = subarray + array

        attributes.append(subarray)
        maxlength = len(attributes[0]) - 12
        energyimport = obscure([x[1] for x in attributes[0][:maxlength]])
        energyimporttime = [(x[2] - starttime)/3600000 for x in attributes[0][:maxlength]]


    # Calculating total energy used during the run
    try:
        energyused = sf.twoDecimals((energyimport[-1] - energyimport[0])/1000)
    except:
        energyused = 0


    # Setting a font size for all y axis labels, and distance between ticks and gridlines on x axis
    font_size = 16
    xticks = 3
    minorLocator = MultipleLocator(1)

    # Cooling type will be forced cooling unless otherwise specified
    coolingtype = 'Forced Cooling'

    # Making a function that just gets the endspots
    def getEndspots():
        global avgrates
        global endspots
        avgrates = []
        endspots = []
        # if reporttype == 'full':
        #     firsttemp = (tempsf[0] + tempsc[0] + tempsr[0]) / 3
        #     firsttime = tempsftimeselapsed[0]
        # else:
        firsttemp = furnacetemperature[0]
        firsttime = furnacetemperaturetime[0]
        totaltime = 0

        # At the end of each step, calculate the change in temp, and divide by time to get average rate of change
        # Also determine where each step ends, and call it an endspot
        # if reporttype == 'full':
        #     for element in currentsetpointlist[1:]:

        #         # Endspot is determined as the list index where the total elapsed time matches (or is close to matching) 
        #         # the elapsed time of all setpoints added up
        #         endspot = bisect_left(furnacetemperaturetime,(element[2] + totaltime) / 60)

        #         # Calculations for average rate, which is (change in temp) / (change in time)
        #         lasttemp = (tempsf[endspot-36] + tempsc[endspot-36] + tempsr[endspot-36]) / 3 
        #         lasttime = furnacetemperaturetime[endspot-36] 
        #         tempdifference = lasttemp - firsttemp 
        #         timedifference = (lasttime - firsttime) * 60 
        #         rate = tempdifference/timedifference
        #         avgrates.append(rate)

        #         # If the endspot is at the very end of the run, then change it to being 3 minutes before
        #         if endspot + 37 <= len(tempsf) - 1:
        #             endspot = endspot
        #         else:
        #             endspot = endspot - 38
                
        #         # Updating values to be used during the next iteration of the loop
        #         firsttemp = (tempsf[endspot+37] + tempsc[endspot+37] + tempsr[endspot+37]) / 3
        #         firsttime = furnacetemperaturetime[endspot+37]
        #         totaltime = totaltime + element[2]

        #         # Putting the endspot into the list of endspots
        #         endspots.append(endspot)

        # # For all other types of reports, then use the furnace temperature instead
        # else:
        for element in currentsetpointlist[1:]:
            # Endspot is determined as the list index where the total elapsed time matches (or is close to matching) 
            # the elapsed time of all setpoints added up
            endspot = bisect_left(furnacetemperaturetime,(element[2] + totaltime) / 60)

            # Calculations for average rate, which is (change in temp) / (change in time)
            lasttemp = furnacetemperature[endspot-36]
            lasttime = furnacetemperaturetime[endspot-36] 
            tempdifference = lasttemp - firsttemp 
            timedifference = (lasttime - firsttime) * 60 
            rate = tempdifference/timedifference
            avgrates.append(rate)

            # If the endspot is at the very end of the run, then change it to being 3 minutes before
            if endspot + 37 <= len(furnacetemperature) - 1:
                endspot = endspot
            else:
                endspot = endspot - 38
            
            # Updating values to be used during the next iteration of the loop
            firsttemp = furnacetemperature[endspot+37]
            firsttime = furnacetemperaturetime[endspot+37]
            totaltime = totaltime + element[2]

            # Putting the endspot into the list of endspots
            endspots.append(endspot)


    # Now creating all of the functions for each section of the report, since all necessary data has been loaded in

    #########################
    # Thermocouple Position #
    #########################

    def tcpositions():

        global tempsf
        global tempsc
        global tempsr
        global probedata
        probedata = []

        # Finding run information from eq_sintering_furnaces based on batch ID, 
        # then using that to get all info from eq_sintering_furnaces_datalogger
        cur.execute("SELECT experiment_id, max_x, max_y, max_z FROM eq_sintering_furnaces WHERE batch_id='{}'".format(batchid))
        results = cur.fetchall()[0]
        experimentid = results[0]
        max_x = results[1]
        max_y = results[2]
        max_levels = results[3]

        # If nothing is returned for max x, y, and z, then assume 4x8x5
        if max_x == None:
            max_x = 4
        if max_y == None:
            max_y = 8
        if max_levels == None:
            max_levels = 5

        cur.execute("SELECT id, experiment_id, thermocouple, x, y, z, furnace_id, time, cooling_type FROM eq_sintering_furnaces_datalogger WHERE experiment_id='{}'".format(experimentid))
        thermolocations = sf.makeArray(cur.fetchall())

        # Only using entries for the correct sintering furnace
        thermolocations = [x for x in thermolocations if x[6] == (equipment_id-1)]

        # If any of the thermocouple numbers are not present in thermolocations, then remove the corresponding entry from probe_tagids
        for k in range(1,19):
            if k not in [x[2] for x in thermolocations]:
                # Removing the entry from probe_tagids that has the name as "P" + the thermocouple number
                for i in range(len(probe_tagids)):
                    if probe_tagids[i]["name"] == 'P' + str(k):
                        del probe_tagids[i]
                        break


        # If any of the probes have a z value of zero, then change their names to have (front), (center), or (rear)
        for element in thermolocations:
            if element[5] == 0:
                for i in range(len(probe_tagids)):
                    if int(probe_tagids[i]["name"][1:]) == int(element[2]):
                        if element[4] == 16:
                            probe_tagids[i]["name"] = probe_tagids[i]["name"] + ' (Rear)'
                        elif element[4] == 17:
                            probe_tagids[i]["name"] = probe_tagids[i]["name"] + ' (Center)'
                        elif element[4] == 18:
                            probe_tagids[i]["name"] = probe_tagids[i]["name"] + ' (Front)'

        # Getting data for each of the thermocouples that was used in the run
        
        for element in probe_tagids:

            # Getting all tag IDs that are associated with the current element
            tagids = sf.getAllTags(element["tagid"])

            subarray = []
            for table in tables:

                cur.execute("SELECT tagid, intvalue, floatvalue, stringvalue, datevalue, t_stamp FROM {} WHERE tagid IN ({}) AND t_stamp BETWEEN {} AND {} ORDER BY t_stamp ASC".format(table,tagids,starttime,stoptime))
                array = sf.makeArray(cur.fetchall(),removeNone=True)
                subarray = subarray + array

            # Obscuring the temperature data
            subarray = [[x[0],x[1]*tempmultiplier,x[2]] for x in subarray]

            # If this probe was used as a front, center, or rear reference thermocouple, then assign it its own variable
            if ' (Rear)' in element["name"]:
                tempsr = subarray
            elif ' (Center)' in element["name"]:
                tempsc = subarray
            elif ' (Front)' in element["name"]:
                tempsf = subarray

            probedata.append(subarray)

        # If nothing was added to the probedata list, then quit
        print(len(probedata))
        print('\n\n\n')
        if len(probedata) == 0:
            print('No temperature probes were used in this run. Try making a single report instead')
            quit()


        # Creating array filled with locations
        locations = np.zeros((max_levels,max_x,max_y))

        for element in thermolocations:
            for k in range(1,max_levels+1):
                for i in range(1,max_x+1):
                    for j in range(1,max_y+1):
                        if i == element[3] and j == element[4] and k == element[5]:
                            locations[k-1,i-1,j-1] = int(element[2])

        # Creating max_levels sets of 2 tables, one for each level of the furnace
        # If the position of a table cell contains a thermocouple, then the thermocouple number will be printed in the table cell
        # If the position of a table cell does not contain a thermocouple, then the table cell will be blank
        # The first table will be the front of the furnace, and the second table will be the back of the furnace
        # Creating a header
        sf.writeHeader(pdf,'Thermocouple Positions')
        pdf.ln(10)
        top = pdf.get_y()

        # Setting the maximum height and width of each furnace layer table when printed on the PDF
        max_height = 32
        max_width = 64

        for k in range(max_levels):

            # After the third table is created, place the 4th and 5th off to the right
            if k == 3:
                pdf.set_xy(100,top)
            elif k >= 4:
                pdf.set_x(100)

            # Writing which level the table corresponds to
            pdf.set_font('Helvetica','B',10)
            pdf.write(10,'Level {}:\n'.format(k+1))
            pdf.set_font('Helvetica','',10)

            # Creating the tables
            # Place the first 3 tables on the left side of the page, and the last 2 on the right side
            if k < 3:
                for i in range(max_x):
                    for j in range(max_y):
                        if locations[k,i,j] != 0:
                            pdf.cell((max_width/max_y),(max_height/max_x),txt=str(int(locations[k,i,j])),border=1,align='C')
                        else:
                            pdf.cell((max_width/max_y),(max_height/max_x),txt='-',border=1,align='C')
                    pdf.ln()

            else:
                for i in range(max_x):
                    pdf.set_x(100)
                    for j in range(max_y):
                        if locations[k,i,j] != 0:
                            pdf.cell((max_width/max_y),(max_height/max_x),txt=str(int(locations[k,i,j])),border=1,align='C')
                        else:
                            pdf.cell((max_width/max_y),(max_height/max_x),txt='-',border=1,align='C')
                    pdf.set_x(100)
                    pdf.ln()


    ##############
    # Fill Color #
    ##############

    # Function that changes the fill color of the pdf
    def fillColor(color, pdf=pdf):

        if color == 'light blue':
            pdf.set_fill_color(240,248,255)
        elif color == 'light green':
            pdf.set_fill_color(153,255,204)
        elif color == 'light yellow':
            pdf.set_fill_color(255,255,153)
        elif color == 'light orange':
            pdf.set_fill_color(255,204,153)
        elif color == 'light gray':
            pdf.set_fill_color(230,230,230)
        elif color == 'gray orange':
            pdf.set_fill_color(230,184,138)
        elif color == 'gray':
            pdf.set_fill_color(202,202,202)


    ############################
    # Block Delta Temperatures #
    ############################

    # Finding the temperature range of the thermocouples that are in blocks
    def getBlockDeltas():

        # Returns array full of triples that contain (delta temperature,hottest thermocouple,coolest thermocouple) for all temperature measurements
        global blockdeltas
        blockdeltas = []

        for k in range(len(probedata[0]) - 5):
            array = []

            for probe in probedata:
                temp = probe[k][1]
                array.append(temp)
            
            blockdeltas.append(sf.minmax(array))

        global blockdeltatemps
        blockdeltatemps = [x[0] for x in blockdeltas[:maxlength]]


    #########################
    # Setpoint temperatures #
    #########################

    def setpointTemperatures(halfsize=False):

        try:
            # Plotting setpoint temperature values
            fig, ax1 = sf.createPlot(x=[settimes], y=[settemps], xlabel='Time Elapsed (Hours)', ylabel='Temperature (C)')
            ax1.grid(which = 'minor', linestyle=':')

            plt.savefig(filepath + 'setpoints' + iteration + '.png',bbox_inches='tight',dpi=200)
            
            # Add plot to PDF
            ploty = pdf.get_y() + 15
            sf.addPlot(pdf, 'Furnace Setpoint Temperature',filepath + 'setpoints' + iteration + '.png', halfsize=halfsize)
            
            # Add table to PDF
            if halfsize == False:
                sf.makeTable(pdf, ['Step Number','Temp (C)','Time (min)','Prev Temp','Prev Time'],setpointlist[1:],labelwidth=18,datawidth=18,titlewrap=1,halfsize=halfsize)

            else:
                # Setting the x and y values so that the table ends up next to the plot
                pdf.set_xy(100,ploty)

                # Making a list of setpoints just for the current run and not the previous, and then making a table from it
                justcurrentsetpoints = [item[:3] for item in currentsetpointlist[1:]]
                sf.makeTable(pdf,['Step Number','Temp (Celsius)','Time (min)'],justcurrentsetpoints,labelwidth=18,datawidth=16,titlewrap=1,halfsize=halfsize)
            
                # Setting the y position of PDF to be at least as low as the plot, or else the table. Whichever is lower
                if pdf.get_y() <= ploty + 72:
                    pdf.set_y(ploty + 72)

            ax1.clear()
            plt.cla()

        except:
            # Printing to the PDF that there was an error
            sf.writeHeader(pdf,'Furnace Setpoint Temperature',halfsize=halfsize)
            pdf.write(10,'Unable to create setpoint temperature plot or table.\n\n')
            # Printing to the console
            print('Unable to create setpoint temperature plot or table.\n')


    ##############################
    # Furnace Actual Temperature #
    ##############################

    def actualTemperature(halfsize=False, xadjust=0, yadjust=0):

        try:
            if reporttype == 'single':
                # Plotting temperature values based on only the furnace thermocouple
                fig, ax1 = sf.createPlot(x=[furnacetemperaturetime], y=[furnacetemperature], labels=['Furnace TC'], xlabel='Time Elapsed (Hours)', ylabel='Temperature (C)')

            else:
                # Plotting actual temperature values if they exist
                try:
                    # for k in range(5,8):
                    #     if k in [x[2] for x in thermolocations]
                    fig, ax1 = sf.createPlot(x=[[(x[2] - starttime)/3600000 for x in tempsf[:maxlength]],
                                                [(x[2] - starttime)/3600000 for x in tempsc[:maxlength]],
                                                [(x[2] - starttime)/3600000 for x in tempsr[:maxlength]],
                                                furnacetemperaturetime], 
                                            y=[[x[1] for x in tempsf[:maxlength]],
                                                [x[1] for x in tempsc[:maxlength]],
                                                [x[1] for x in tempsr[:maxlength]],
                                                furnacetemperature], 
                                                labels=['Front Temperature (P18)','Center Temperature (P17)','Rear Temperature (P16)','Furnace TC'],
                                                xlabel='Time Elapsed (Hours)', ylabel='Temperature (C)')
                except:
                    # Just plotting the furnace thermocouple if unable to plot data from the F, C, R probes
                    fig, ax1 = sf.createPlot(x=[furnacetemperaturetime], y=[furnacetemperature], labels=['Furnace TC'], xlabel='Time Elapsed (Hours)', ylabel='Temperature (C)')


            # Set grid to use minor tick locations. 
            ax1.grid(which = 'minor', linestyle=':')
            legend = ax1.legend(loc='best')

            plt.savefig(filepath + 'actualtemp' + iteration + '.png',bbox_inches='tight')
            ax1.clear()
            plt.cla()
            legend.remove()

            # Add plot to PDF
            sf.addPlot(pdf, 'Furnace Actual Temperature',filepath + 'actualtemp' + iteration + '.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust)

        except:
            # Printing to the PDF that there was an error
            sf.writeHeader(pdf,'Furnace Actual Temperature',halfsize=halfsize)
            pdf.write(10,'Unable to create actual temperature plot.\n\n')
            # Printing to the console
            print('Unable to create actual temperature plot.\n')


    ###################################
    # Setpoint vs actual temperatures #
    ###################################

    def setpointVActualTemperatures(halfsize=False, xadjust=0, yadjust=0):

        # try:
        # Plotting actual temp vs setpoint values
        fig, ax1 = plt.subplots(figsize=(10,6))
        ax1.grid(linestyle='--',linewidth=1.0)
        minorLocator = MultipleLocator(1)
        ax1.xaxis.set_minor_locator(minorLocator)

        # Set grid to use minor tick locations. 
        ax1.grid(which = 'minor', linestyle=':')
        ax1.plot(settimes,settemps,'k--', label = 'Setpoint Temperatures')

        # Plotting temperature from the thermocouple data if the report type is 'full'
        if reporttype == 'full':
            # Plotting temperature data from the probedata array, with the label being the thermocouple number
            for probe in probedata:

                # Creating a label for the thermocouple number by matching the tagid with the name in probe_tagids
                for element in probe_tagids:
                    if element["tagid"] == str(probe[0][0]):
                        label = str(element["name"])
                        break
                    else:
                        label = probe[0][0]

                # Plotting the temperature data
                ax1.plot([(x[2] - starttime)/3600000 for x in probe],[x[1] for x in probe], label = label)

            # If the front thermocouple data is available, then plot all 18 thermocouples
            # if len(tempsf) > 0:
            #     for k in range(5,23):
            #         if k == 5:
            #             label = 'Front Temperature (P18)'
            #         elif k == 6:
            #             label = 'Center Temperature (P17)'
            #         elif k == 7:
            #             label = 'Rear Temperature (P16)'
            #         else:
            #             label = 'P' + str(k-7)
            #         ax1.plot([(x[2] - starttime)/3600000 for x in attributes[k]],obscure([x[1] for x in attributes[k]],type='temperature'),label = label)

        # Also plotting the temperature of the furnace thermocouple for all report types
        ax1.plot(furnacetemperaturetime,obscure(furnacetemperature,type='temperature'),color='red',label='Furnace TC')

        ax1.set_xlabel('Time Elapsed (Hours)',fontsize=font_size)
        ax1.set_ylabel('Temperature (C)', fontsize=font_size)

        # Creating a secondary axis and plotting the vacuum levels on it
        ax2 = ax1.twinx()
        ax2.plot(vacuumtime,vacuum,'b',label='Vacuum')
        ax2.set_ylabel('Vacuum (mbar)', fontsize=font_size)
        # Changing the axis to log
        ax2.set_yscale('log')
        # Plotting empty line to create a legend for the vacuum
        ax1.plot([],[],'b',label='Vacuum')


        # Shrink current axis' height by 10% on the bottom
        box = ax1.get_position()
        ax1.set_position([box.x0, box.y0 + box.height * 0.1,
                        box.width, box.height * 0.9])

        # Put a legend below current axis
        legend = ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15),
                fancybox=True, shadow=True, ncol=5)

        plt.savefig(filepath + 'setpointvactual' + iteration + '.png',bbox_inches='tight')
        ax1.clear()
        plt.cla()
        legend.remove()

        # Add plot to PDF
        sf.addPlot(pdf, 'Setpoint vs Actual Temperatures',filepath + 'setpointvactual' + iteration + '.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust)

        # except:
        #     # Printing to the PDF that there was an error
        #     sf.writeHeader(pdf,'Setpoint vs Actual Temperatures',halfsize=halfsize)
        #     pdf.write(10,'Unable to create setpoint vs actual temperature plot.\n\n')
        #     # Printing to the console
        #     print('Unable to create setpoint vs actual temperature plot.\n')

        

    ##############################
    # Interactive Temp vs Vacuum #
    ##############################

    def interactivePlot():
        
        # # Getting the endspots if they have not already been gotten
        # getEndspots()
        # # Inserting a value of 0 at the beginning of the endspots list
        # endspots.insert(0,0)
        # # Removing the 5th entry in the endspots list, since it is not needed
        # endspots.pop(5)
        # # Adding 2 more hours of time to the 5th endspot
        # endspots[4] = endspots[4] + 2*60*12
        # # Adding 3 more minutes of time to the 9th endspot
        # endspots[8] = endspots[8] + 3*12
        # # Adding 3 more minutes of time to the 11th endspot
        # endspots[10] = endspots[10] + 3*12
        # # Adding 4 more minutes of time to the 13th endspot
        # endspots[12] = endspots[12] + 3*12
        # # Adding 5 more minutes of time to the 15th endspot
        # endspots[14] = endspots[14] + 3*12


        # # printing the endspots
        # print('Endspots: {}'.format(endspots))

        # b230262endpoints = [383,1367,2171,2614,5835,14485,17120,
        #              23112,24490,25704,27389,28571,30020,31087,32409,33360,33893]

        
        # # A plot will be created to show the setpoint temperature between every set of 2 endspots
        # # The plot will also show the actual temperature between every set of 2 b230262endpoints

        # for k in range(int((len(endspots)-1)/2)):
        #     # Getting the setpoint temperatures between the current endspot and 2 endspots ahead
        #     setpointtemps = settemps[endspots[2*k]:endspots[2*k+2]]
        #     setpointtimes = settimes[endspots[2*k]:endspots[2*k+2]]

        #     # Creating a new list of setpointtimes that begins at 0 and increases to the total elapsed time for that step
        #     setpointtimes = [x - setpointtimes[0] for x in setpointtimes]

        #     # Getting the actual temperatures between the current and next b230262 endpoint
        #     actualtemps = furnacetemperature[b230262endpoints[2*k]:b230262endpoints[2*k+2]]
        #     actualtimes = furnacetemperaturetime[b230262endpoints[2*k]:b230262endpoints[2*k+2]]
        #     actualtimes = [x - actualtimes[0] for x in actualtimes]

        #     # Getting the vacuum levels between the current and next b230262 endpoint
        #     vacuumlevels = vacuum[b230262endpoints[2*k]:b230262endpoints[2*k+2]]
        #     vacuumtimes = vacuumtime[b230262endpoints[2*k]:b230262endpoints[2*k+2]]
        #     vacuumtimes = [x - vacuumtimes[0] for x in vacuumtimes]

        #     # Calculating the amount of time taken for the setpoint as well as the actual temperature from start to finish of the section
        #     if k == 0:
        #         setpointtime = setpointlist[2*k+1][2] + setpointlist[2*k+2][2]
        #         steps = 'Steps 1 and 2'
        #     elif k == 1:
        #         setpointtime = setpointlist[2*k+1][2] + setpointlist[2*k+2][2] + setpointlist[2*k+3][2]
        #         steps = 'Steps 3, 4, and 5'
        #     else:
        #         setpointtime = setpointlist[2*k+2][2] + setpointlist[2*k+3][2]
        #         steps = 'Steps {} and {}'.format(2*k+2,2*k+3)
        #     actualtime = round((actualtimes[-1] - actualtimes[0]) * 60,2)
        #     timedifference = round(actualtime - setpointtime,2)

        #     # Calculating the minimum and maximum vacuum levels during the section
        #     minvacuum = round(min(vacuumlevels),5)
        #     maxvacuum = round(max(vacuumlevels),5)

        # # Plotting the setpoint and actual temperatures
        # fig, ax1 = plt.subplots(figsize=(10,6))
        # ax1.grid(linestyle='--',linewidth=1.0)
        # minorLocator = MultipleLocator(1)
        # ax1.xaxis.set_minor_locator(minorLocator)

        # ax1.plot(setpointtimes,setpointtemps,'k--', label = 'Setpoint Temperatures')
        # ax1.plot(actualtimes,actualtemps,color='red',label='Furnace TC')

        # ax1.set_xlabel('Time Elapsed (Hours)',fontsize=font_size)
        # ax1.set_ylabel('Temperature (C)', fontsize=font_size)

        # # Creating a secondary y axis and plotting the vacuum levels on it
        # ax2 = ax1.twinx()
        # ax2.plot(vacuumtimes,vacuumlevels,'b',label='Vacuum')
        # ax2.set_ylabel('Vacuum (mbar)', fontsize=font_size)
        # # Changing the axis to log
        # ax2.set_yscale('log')
        # # Setting the range of the y axis to be between 10^-5 and 100
        # ax2.set_ylim([10**-5,100])
        # # Plotting empty line to create a legend for the vacuum
        # ax1.plot([],[],'b',label='Vacuum')

        # legend = ax1.legend(loc='best')

        # plt.savefig(filepath + 'setpointvactualstep' + str(k) + '.png',bbox_inches='tight')
        # ax1.clear()
        # plt.cla()
        # legend.remove()

        # # Add plot to PDF
        # sf.addPlot(pdf, 'Setpoint vs Actual Temperatures - ' + steps,filepath + 'setpointvactualstep' + str(k) + '.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust)

        # # Adding a table to the PDF
        # # sf.makeTable(pdf,['Setpoint Time (minutes)','Actual Time (minutes)','Time Difference (minutes)','Min Vacuum (mbar)','Max Vacuum (mbar)'],[[setpointtime,actualtime,timedifference,minvacuum,maxvacuum]],labelwidth=28,datawidth=28,titlewrap=1,halfsize=halfsize)

        # header = ['Setpoint Time','Actual Time','Time Difference','Min Vacuum','Max Vacuum']
        # data = [setpointtime,actualtime,timedifference,minvacuum,maxvacuum]

        # # Setting fontsize to 10
        # pdf.set_font('Helvetica','',10)
        # pdf.ln(10)

        # for i in range(len(header)):
        #     pdf.cell(38,10,txt=header[i],border=1,align='C',fill=True)
        # pdf.ln()
        # for i in range(len(data)):
        #     # Determining the unit based on i
        #     if i == 0 or i == 1 or i == 2:
        #         unit = ' minutes'
        #     else:
        #         unit = ' mbar'
        #     pdf.cell(38,10,txt=str(data[i]) + unit,border=1,align='C')
        






        # Creating a new setpoints list with a new recipe (10/24/2023)
        newsetpoints = [['Step 0', 20, 0, 20, 0], 
                        ['Step 1', 244, 78, 280, 90], 
                        ['Step 2', 265, 21, 280, 15], 
                        ['Step 3', 265, 171, 265, 40], 
                        ['Step 4', 590, 325, 265, 150], 
                        ['Step 5', 590, 300, 265, 120], 
                        ['Step 6', 675, 85, 590, 110], 
                        ['Step 7', 675, 180, 590, 220], 
                        ['Step 8', 775, 100, 675, 85], 
                        ['Step 9', 775, 120, 675, 115], 
                        ['Step 10', 965, 190, 775, 100], 
                        ['Step 11', 965, 90, 775, 140], 
                        ['Step 12', 1087, 80, 875, 100], 
                        ['Step 13', 1087, 60, 875, 120]]
        
        # Creating a second new setpoints list with an additional step near beginning (10/26/2023)
        newsetpoints2 = [['Step 0', 20, 0, 20, 0], 
                        ['Step 1', 244, 78, 280, 90], 
                        ['Step 2', 265, 21, 280, 15], 
                        ['Step 3', 265, 90, 265, 40],
                        ['Step 4', 405, 140, 0, 0],
                        ['Step 5', 405, 81, 0, 0],
                        ['Step 6', 590, 185, 265, 150], 
                        ['Step 7', 590, 300, 265, 120], 
                        ['Step 8', 675, 85, 590, 110], 
                        ['Step 9', 675, 180, 590, 220], 
                        ['Step 10', 775, 100, 675, 85], 
                        ['Step 11', 775, 120, 675, 115], 
                        ['Step 12', 965, 190, 775, 100], 
                        ['Step 13', 965, 90, 775, 140], 
                        ['Step 14', 1087, 80, 875, 100], 
                        ['Step 15', 1087, 60, 875, 120]]


        # Creating another set of setpoints 11/3/2023 Updated 11/9/2023 so 1070 is held for 100 minutes instead of 160
        newsetpoints4 = [['Step 0', 20, 0], 
                        ['Step 1', 244, 78], 
                        ['Step 2', 265, 21], 
                        ['Step 3', 265, 90],
                        ['Step 4', 405, 140],
                        ['Step 5', 405, 81],
                        ['Step 6', 590, 185], 
                        ['Step 7', 590, 240], 
                        ['Step 8', 675, 85], 
                        ['Step 9', 675, 180], 
                        ['Step 10', 775, 29], 
                        ['Step 11', 775, 220], 
                        ['Step 12', 965, 55], 
                        ['Step 13', 965, 190], 
                        ['Step 14', 1070, 10], 
                        ['Step 15', 1070, 100],
                        ['Step 16', 1130, 10],
                        ['Step 17', 1130, 90]]
        
        # Creating a new setpoints list with a new recipe (11/6/2023) for Annealing 820 - 2 step B230367
        newsetpoints5 = [['Step 0', 20, 0], 
                        ['Step 1', 750, 250], 
                        ['Step 2', 895, 50], 
                        ['Step 3', 895, 140],
                        ['Step 4', 695, 90],
                        ['Step 5', 695, 90]]
        

        # Creating a new setpoints list with a new recipe (11/6/2023) for AAA Annealing 820 - 1 step B230422
        newsetpoints6 = [['Step 0', 20, 0], 
                        ['Step 1', 680, 194], 
                        ['Step 2', 895, 145], 
                        ['Step 3', 895, 210]]


        # Turning these setpoints into newsettimes and newsettemps
        newsettimes,newsettemps = sf.expandSetpoints(newsetpoints,templocation=1,timelocation=2)
        newsettimes6,newsettemps6 = sf.expandSetpoints(newsetpoints6, templocation=1, timelocation=2)
        newsettimes5, newsettemps5 = sf.expandSetpoints(newsetpoints5, templocation=1, timelocation=2)

        # Doing the same thing but in plotly and then saving as html
        print('Creating setpoint vs actual temperature plot in plotly')

        # Points where the vacuum level is at a peak or valley
        b230262peaks = [708,1534,1766,2041,2074,2339,4908,5889,6479,7209,10475,10618,11140,11469,12842,12976,
                        13586,14433,15019,17141,18312,20807,20887,21662,23071,23428,24528,25327,
                        25332,26024,28287,29290,30320,31096,32406,33442,33893,33896]
        
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=furnacetemperaturetime[:len(settemps)], y=settemps, name='Setpoint Temperature'))
        fig.add_trace(go.Scatter(x=furnacetemperaturetime[:len(newsettemps5)], y=newsettemps6, name='New Setpoint Temperature', line_color='black'))
        fig.add_trace(go.Scatter(x=furnacetemperaturetime, y=furnacetemperature, name='Furnace Temperature', line_color='red'))
        # Adding a secondary y axis to the plot, and plotting the pressure on it
        fig.add_trace(go.Scatter(x=furnacetemperaturetime[:len(vacuum)], y=vacuum, name='Vacuum', line_color='green', yaxis='y2'))
        
        # Making the lines thinner than they are currently
        fig.update_traces(line=dict(width=0.7))

        # Changing just the vacuum line to have a thickness of 0.4
        fig.update_traces(selector=dict(name='Vacuum'), line=dict(width=0.4))
        
        # fig.add_trace(go.Scatter(x=[k for k in range(len(settemps))], y=settemps, name='Setpoint Temperature'))
        # fig.add_trace(go.Scatter(x=[j for j in range(len(furnacetemperature))], y=furnacetemperature, name='Furnace Temperature'))
        # # Addding a secondary y axis to the plot, and plotting the pressure on it
        # fig.add_trace(go.Scatter(x=[i for i in range(len(vacuum))], y=vacuum, name='Vacuum', yaxis='y2'))

        
        # Moving y2 axis to the right side of the plot
        fig.update_layout(yaxis2=dict(anchor='x', overlaying='y', side='right', range=[-5,2]))

        # Adding a title and axis labels
        fig.update_layout(title='Temperature and Pressure vs Time' + ' - ' + batchid,
                        xaxis_title='Elapsed Time (Hours)',
                        yaxis_title='Temperature (C)',
                        yaxis2_title='Pressure (mbar)')


        # Adding a legend
        fig.update_layout(legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ))

        # Adding vertical grid lines every 5 hours on the x axis
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', tickmode='linear', tick0=0, dtick=5)


        # Changing only yaxis2 to be on a log scale
        fig.update_layout(yaxis2_type="log")
        

        
        # # For every peak or valley in the vacuum, annotate the point with the vacuum value in scientific notation and an arrow pointing to the point
        # for k in b230262peaks:
        #     # If the index of k in b230262peaks is even, then a is 2 and b is -40
        #     if b230262peaks.index(k) % 2 == 0:
        #         a = -10
        #         b = -40
        #     # If the index of k in b230262peaks is odd, then a is 2 and b is 40
        #     else:
        #         a = -10
        #         b = 40
        #     fig.add_annotation(x=vacuumtime[k], y=math.log10(vacuum[k]), xref='x', yref='y2', text="{:.5f}".format(vacuum[k]), showarrow=True, arrowhead=7, ax=a, ay=b)
        
        
        # Changing the information written when hovering over the data points to showing the temperature as the y value, and the pressure as the y2 value, and the time as the x value
        fig.update_layout(hovermode="x unified")

        # Saving the figure as an html file
        pio.write_html(fig, file=filepath + batchid + 'TempvsVacuum.html')

        # Displaying the figure
        fig.show()
        
    # interactivePlot()
    #################################################
    # Max and min delta temperatures between blocks #
    #################################################

    def minMaxDeltaTemps():

        # try:
        # Getting a list of endspots if it does not currently exist
        getEndspots()

        # Finding the temperature range of just the 15 thermocouples in blocks
        # Returns array full of triples that contain (delta temperature,hottest thermocouple,coolest thermocouple) for all temperature measurements
        getBlockDeltas()

        # Create arrays for delta block temperatures throughout each setpoint step
        startpoint = 0
        stepdeltas = []

        for element in endspots:
            array = []
            for item in blockdeltas[startpoint:element]:
                array.append(item)

            startpoint = element
            stepdeltas.append(array)


        # Finding largest and smallest delta temperature points within each step
        def sort_key(deltapoint):
            return deltapoint[0]

        minmaxdeltas = []
        for element in stepdeltas:
            if len(element) > 0:
                least = min(element,key = sort_key)
                most = max(element,key = sort_key)
                minmaxdeltas.append([least,most])

        # Creating list with minimum and maximum delta temperatures between blocks at each step
        k = 1
        minmaxdfinfo = []

        for element in minmaxdeltas:

            # Finding the two thermocouples that correspond to delta min
            for item in probe_tagids:

                if str(item["tagid"]) == str(probedata[element[0][1]][0][0]):
                    mina = item["name"][1:]
                    break

            for item in probe_tagids:
                if str(item["tagid"]) == str(probedata[element[0][2]][0][0]):
                    minb = item["name"][1:]
                    break

            # Finding the two thermocouples that correspond to delta max
            for item in probe_tagids:
                if str(item["tagid"]) == str(probedata[element[1][1]][0][0]):
                    maxa = item["name"][1:]
                    break

            for item in probe_tagids:
                if str(item["tagid"]) == str(probedata[element[1][2]][0][0]):
                    maxb = item["name"][1:]
                    break

            # Appending the information to minmaxdfinfo
            minmaxdfinfo.append([str(k),sf.twoDecimals(element[0][0]), mina + '-' + minb, sf.twoDecimals(element[1][0]),maxa + '-' + maxb])
            k = k + 1


        # For each step in minmaxdfinfo, inserting the temperature setpoint
        for k in range(len(minmaxdfinfo)):
            minmaxdfinfo[k].insert(1,setpointlist[k+1][1])

            # Then, inserting whether the setpoint went up, down, or held constant since the last setpoint
            # For the first step, just say it went up
            if k == 0:
                minmaxdfinfo[k].insert(2,'Up')
            else:
                if currentsetpointlist[k+1][1] > currentsetpointlist[k][1]:
                    minmaxdfinfo[k].insert(2,'Up')
                elif currentsetpointlist[k+1][1] < currentsetpointlist[k][1]:
                    minmaxdfinfo[k].insert(2,'Down')
                else:
                    minmaxdfinfo[k].insert(2,'Hold')


        # Creating header for the section
        sf.writeHeader(pdf, 'Minimum and Maximum Delta Temperatures Between Blocks')

        # Making a list of column names to be used in the table
        pdf.set_font('Helvetica','',8.5)
        columnnames = ['Step     ','Temp     ','Type      ','Delta Min','Min Probe','Delta Max','Max Probe']
        sf.makeTable(pdf, columnnames,minmaxdfinfo,labelwidth=13,datawidth=13, titlewrap=1, fontsize=9)


        # except:
        #     # Printing to the PDF that there was an error
        #     sf.writeHeader(pdf,'Minimum and Maximum Delta Temperatures Between Blocks')
        #     pdf.write(10,'Unable to create minimum and maximum delta temperatures between blocks table.\n\n')
        #     # Printing to the console
        #     print('Unable to create minimum and maximum delta temperatures between blocks table.\n')


    ###################################################
    # Setpoint vs actual temperatures (min, max, avg) #
    ###################################################

    def setVActualAbv(halfsize=False, xadjust=0, yadjust=0):

        try:
            # Finding the hottest and coolest blocks, and average temperature of all blocks
            # Also finding the delta temperature between hottest and coldest blocks
            hottestCoolest()

            # Plotting min, max, and avg actual temp vs setpoint values
            fig, ax1 = sf.createPlot(x=[settimes,blockdeltatimeselapsed,blockdeltatimeselapsed,blockdeltatimeselapsed],
                                    y=[settemps, hottest, coolest, averagetemp], labels=['Setpoint Temperature','Hottest Block Temperature',
                                    'Coolest Block Temperature', 'Average Block Temperature'], xlabel='Time Elapsed (Hours)', ylabel='Temperature (C)')

            # Set grid to use minor tick locations. 
            ax1.grid(which = 'minor', linestyle=':')

            # Shrink current axis' height by 10% on the bottom
            box = ax1.get_position()
            ax1.set_position([box.x0, box.y0 + box.height * 0.1,
                            box.width, box.height * 0.9])

            # Put a legend below current axis
            legend = ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15),
                    fancybox=True, shadow=True, ncol=2)

            plt.savefig(filepath + 'hottestandcoldest' + iteration + '.png',bbox_inches='tight')
            ax1.clear()
            plt.cla()
            legend.remove()

            # Add plot to PDF
            sf.addPlot(pdf, 'Setpoint vs Actual Block Temperatures (max, avg, min)',filepath + 'hottestandcoldest' + iteration + '.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust)
            pdf.set_y(190)

        except:
            # Printing to the PDF that there was an error
            sf.writeHeader(pdf,'Setpoint vs Actual Temperatures (max, avg, min)',halfsize=halfsize)
            pdf.write(10, 'Unable to create Setpoint Vs Actual Temperature plot.\n\n')
            # Printing to the console
            print('Unable to create Setpoint Vs Actual Block Temperature plot.\n')


    ##########################
    # Fan rpm during cooling #
    ##########################

    def rpmDuringCooling(halfsize=False, xadjust=0, yadjust=0):

        try:
            # Plotting cooling fan RPM at the end of the run (during cooling)
            # First making arrays of fan RPM cooling information just for the part of the run where cooling occurs
            # Also making arrays for average block temperature and argon pressure for cooling portion of run

            # Finding the hottest and coolest blocks, and average temperature of all blocks
            # Also finding the delta temperature between hottest and coldest blocks
            # hottestCoolest()

            # global endcoolingrpm
            # global endcoolingrpmtime
            # global endavgtemps
            # global endpressure

            # endcoolingrpm = []
            # endcoolingrpmtime = []
            # endavgtemps = []
            # endpressure = []
            # for k in range(len(coolingrpmtimeselapsed)-5):
            #     if coolingrpmtimeselapsed[k] > settimes[-2]:
            #         endcoolingrpm.append(coolingrpm[k])
            #         endcoolingrpmtime.append(coolingrpmtimeselapsed[k])
            #         try:
            #             endavgtemps.append(averagetemp[k])
            #         except:
            #             pass
            #         endpressure.append(pressure[k])
                    
            # # If there is no data at the end of the run, fill the lists with zeros
            # if len(endcoolingrpm) == 0:
            #     endcoolingrpm = [0,0,0]
            #     endcoolingrpmtime = [0,0,0]
            #     endavgtemps = [0,0,0]
            #     endpressure = [0,0,0]


            # Finding the point in time during the run at which the maximum furnace temperature is reached.
            # The cooling fan RPM data will be plotted from this point onward
            # This is done by finding the index of the maximum furnace temperature, and then finding the time at that index
            global maxtempindex
            maxtempindex = np.argmax(furnacetemperature)

            fig, ax1 = plt.subplots(figsize=(10,6))
            ax1.grid(linestyle='--', linewidth=1)
            ax2 = ax1.twinx()

            # # If the average block temperature is available, then plot it
            # if len(endavgtemps) > 0:
            #     ax2.plot(endcoolingrpmtime,endavgtemps,color='red',label = 'Average Block Temperature')
            #     ax1.plot([],[],color='red',label = 'Average Block Temperature')
            # # Otherwise plot the furnace thermocouple temperature
            # else:
            ax2.plot(furnacetemperaturetime[maxtempindex-100:],furnacetemperature[maxtempindex-100:],color='red',label = 'Furnace TC Temperature')
            ax1.plot([],[],color='red',label = 'Furnace TC Temperature')
            ax1.plot(coolingrpmtimeselapsed[maxtempindex-100:],coolingrpm[maxtempindex-100:],color='k',label='Cooling Fan RPM')
            ax1.set_ylabel('Fan RPM', fontsize=font_size)
            ax1.set_xlabel('Time Elapsed (Hours)',fontsize=font_size)
            ax2.set_ylabel('Temperature (C)', fontsize=font_size)


            # If fan did not blow, then set axis limits and set cooling type
            global coolingtype
            if max(coolingrpm[maxtempindex-100:]) < 10:
                ax1.set_ylim(-15,400)
                coolingtype = 'Natural Cooling'
            else:
                coolingtype = 'Forced Cooling'

            start, end = ax1.get_ylim()
            ax1.yaxis.set_ticks(np.arange(0, end, 200))

            legend = ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1),
                    fancybox=True, shadow=True, ncol=2)

            plt.savefig(filepath + 'coolingrpm' + iteration + '.png',bbox_inches='tight')
            ax1.clear()
            plt.cla()

            # Add plot to PDF
            sf.addPlot(pdf, 'Fan RPM During Cooling',filepath + 'coolingrpm' + iteration + '.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust)

        except:
            # Printing to the PDF that there was an error
            sf.writeHeader(pdf,'Fan RPM During Cooling',halfsize=halfsize)
            pdf.write(10, 'Unable to create Fan RPM During Cooling plot.\n\n')
            # Printing to the console
            print('Unable to create Fan RPM During Cooling plot.\n')


    ##################################
    # Furnace pressure while cooling #
    ##################################

    def pressureWhileCooling(halfsize=False, xadjust=0, yadjust=0):

        # Currently relies on some info from rpmDuringCooling() function, so that must be run first

        try:
            # Plotting pressure at the end of the run during cooling
            fig, ax1 = plt.subplots(figsize=(10,6))
            ax1.grid(linestyle='--', linewidth=1)
            ax2 = ax1.twinx()

            # # If the average block temperature is available, then plot it
            # if len(endavgtemps) > 0:
            #     ax2.plot(endcoolingrpmtime,endavgtemps,color='red',label = 'Average Block Temperature')
            #     ax1.plot([],[],color='red',label = 'Average Block Temperature')
            # Otherwise plot the furnace thermocouple temperature
            # else:
            ax2.plot(furnacetemperaturetime[maxtempindex-100:],furnacetemperature[maxtempindex-100:],color='red',label = 'Furnace TC Temperature')
            ax1.plot([],[],color='red',label = 'Furnace TC Temperature')

            # Plotting pressure and naming axes
            ax1.plot(pressuretime[maxtempindex-100:],pressure[maxtempindex-100:],color='k',label='Furnace Pressure')
            ax1.set_ylabel('Furnace Pressure (mbar)', fontsize=font_size)
            ax1.set_xlabel('Time Elapsed (Hours)',fontsize=font_size)
            ax2.set_ylabel('Temperature (C)', fontsize=font_size)

            start, end = ax1.get_ylim()
            ax1.yaxis.set_ticks(np.arange(0, end, 100))

            legend = ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1),
                    fancybox=True, shadow=True, ncol=2)

            plt.savefig(filepath + 'coolingpressure' + iteration + '.png',bbox_inches='tight')
            ax1.clear()
            plt.cla()

            # Add plot to PDF
            sf.addPlot(pdf, 'Furnace Pressure While Cooling',filepath + 'coolingpressure' + iteration + '.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust)
        
        except:
            # Printing to the PDF that there was an error
            sf.writeHeader(pdf,'Furnace Pressure While Cooling',halfsize=halfsize)
            pdf.write(10, 'Unable to create Furnace Pressure While Cooling plot.\n\n')
            # Printing to the console
            print('Unable to create Furnace Pressure While Cooling plot.\n')


    #################################
    # Setpoint vs actual ramp rates #
    #################################

    def rampRates(halfsize=False):

        try:
            # Finding setpoint temperature ramp rates
            setpointslopes = []
            for k in range(len(settemps)-1):
                slope = (settemps[k+1] - settemps[k]) / ((settimes[k+1] - settimes[k])*60) # degrees C per minute
                setpointslopes.append([settimes[k+1],slope])
                setpointslopes.append([settimes[k],slope])

            # Finding ramp rates of actual furnace temperatures over one minute intervals
            slopes = []
            # # Using the average of the front, center, and rear temperatures if they are available
            # if len(tempsf) > 0:
            #     for k in range(int((len(tempsf) - 1)/12)):
                    
            #         newtemp = (tempsf[12*(k + 1)] + tempsc[12*(k + 1)] + tempsr[12*(k + 1)]) / 3
            #         oldtemp = (tempsf[12*k] + tempsc[12*k] + tempsr[12*k]) / 3
            #         newtime = sf.getTimeStamp(tempsftimes[12*(k+1)])
            #         oldtime = sf.getTimeStamp(tempsftimes[12*k])
            #         slope = (newtemp - oldtemp)/((newtime - oldtime)/60000) # degrees C per minute
            #         slopes.append([(oldtime - starttime)/3600000,slope])
            #         slopes.append([(newtime - starttime)/3600000,slope])

            # # Using the furnace thermocouple temperature if the other temperatures are not available
            # else:
            for k in range(int((len(furnacetemperature) - 1)/12)):
                newtemp = furnacetemperature[12*(k + 1)]
                oldtemp = furnacetemperature[12*k]
                newtime = sf.getTimeStamp(furnacetcactualtime[12*(k+1)])
                oldtime = sf.getTimeStamp(furnacetcactualtime[12*k])
                slope = (newtemp - oldtemp)/((newtime - oldtime)/60000) # degrees C per minute
                slopes.append([(oldtime - starttime)/3600000,slope])
                slopes.append([(newtime - starttime)/3600000,slope])

            # Finding ramp rates from setpoints over the entire step
            setrates = []
            for k in range(len(currentsetpointlist)-1):
                if currentsetpointlist[k+1][2] != 0:
                    rate = (currentsetpointlist[k+1][1] - currentsetpointlist[k][1]) / currentsetpointlist[k+1][2]
                    setrates.append(rate)

            # Getting a list of endspots if it does not currently exist
            getEndspots()

            # Creating a list containing the setpoint temp change rates, the actual rates, and the difference between them
            allrates = []
            for k in range(len(setrates)):
                allrates.append([str(k + 1),sf.twoDecimals(setrates[k]),sf.twoDecimals(avgrates[k]),sf.twoDecimals(float(sf.twoDecimals(avgrates[k])) - float(sf.twoDecimals(setrates[k])))])

            # Plotting ramp rates
            fig, ax1 = plt.subplots(figsize=(10,6))
            ax1.plot([x[0] for x in setpointslopes],[x[1] for x in setpointslopes],color='black',label='Setpoint Slope')
            ax1.plot([x[0] for x in slopes],[x[1] for x in slopes],color='blue',label='Actual Slope')
            legend = fig.legend(loc='upper center', bbox_to_anchor=(0.5, 0.0),
                    fancybox=True, shadow=True, ncol=2)
            ax1.set_xlabel('Time Elapsed (Hours)',fontsize=font_size)
            ax1.set_ylabel('Ramp Rate (Degrees/Minute)',fontsize=font_size)
            plt.grid(linestyle='--', linewidth=1)
            ax1.xaxis.set_minor_locator(minorLocator)
            # Set grid to use minor tick locations. 
            ax1.grid(which = 'minor', linestyle=':')
            startx, endx = ax1.get_xlim()
            ax1.xaxis.set_ticks(np.arange(0, endx, xticks))
            starty, endy = ax1.get_ylim()
            ax1.set_ylim(-25,25)
            ax1.yaxis.set_ticks(np.arange(-25, endy, 5))
            plt.savefig(filepath + 'rampRates' + iteration + '.png',bbox_inches='tight')
            ax1.clear()
            plt.cla()
            legend.remove()


            # For each step in minmaxdfinfo, inserting the temperature setpoint
            for k in range(len(allrates)):
                allrates[k].insert(1,setpointlist[k+1][1])

                # Then, inserting whether the setpoint went up, down, or held constant since the last setpoint
                # For the first step, just say it went up
                if k == 0:
                    allrates[k].insert(2,'Up')
                else:
                    if currentsetpointlist[k+1][1] > currentsetpointlist[k][1]:
                        allrates[k].insert(2,'Up')
                    elif currentsetpointlist[k+1][1] < currentsetpointlist[k][1]:
                        allrates[k].insert(2,'Down')
                    else:
                        allrates[k].insert(2,'Hold')

            
            # Add plot and table to PDF
            sf.addPlot(pdf, 'Setpoint vs Actual Ramp Rates',filepath + 'rampRates' + iteration + '.png', halfsize=halfsize)
            sf.makeTable(pdf, ['Step        ','Temp        ','Type        ','Set Rate  ','Actual Rate','Error (C/min)'],allrates,labelwidth=15,datawidth=15,titlewrap=1,fontsize=9)

        except:
            # Printing to the PDF that there was an error
            sf.writeHeader(pdf,'Setpoint vs Actual Ramp Rates',halfsize=halfsize)
            pdf.write(10, 'Unable to create Setpoint vs Actual Ramp Rates plot.\n\n')
            # Printing to the console
            print('Unable to create Setpoint vs Actual Ramp Rates plot.\n')


    ############################################################
    # Time probes were within specified temperatures (minutes) #
    ############################################################

    def timeNearSpecTemps(halfsize=False):

        try:
            # Finding all of the temperatures that the setpoints hold constant for a period of time (horizontal parts of graph)
            spectemps = []
            for k in range(1,len(currentsetpointlist)):
                if currentsetpointlist[k-1][1] == currentsetpointlist[k][1]:
                    spectemps.append([currentsetpointlist[k][1],2,5,10])

            # Getting a list of endspots
            getEndspots()

            # Now create spectimes which shows how long each probe was within specified temperature range
            # Also this should not include cooldown times, so create lasttime variable which is when the last endspot occurs
            lasttime = probedata[0][endspots[-1]][2]
            spectimes = []

            for k in range(len(spectemps)):

                for j in range(3):
                    array = [str(spectemps[k][0]) + '+/-' + str(spectemps[k][j+1])]
                    temprange = [spectemps[k][0] - spectemps[k][j + 1], spectemps[k][0] + spectemps[k][j + 1]]
                    
                    for i in range(len(probedata)):
                        probetemp = [tempmultiplier*x[1] for x in probedata[i] if x[2] < lasttime and temprange[0] < tempmultiplier*x[1] < temprange[1]]
                        timeinrange = round(len(probetemp) / 12, 1) # Minutes that probe has been in temperature range
                        array.append(timeinrange)
                    spectimes.append(array)

            # Add header and table to PDF
            sf.writeHeader(pdf, 'Time Probes Were Within Specified Temperatures (Minutes)')
            sf.makeTable(pdf, ['Temp'] + [x["name"] for x in probe_tagids],spectimes,labelwidth=17,datawidth=11,fontsize=9)

        except:
            # Printing to the PDF that there was an error
            sf.writeHeader(pdf,'Time Probes Were Within Specified Temperatures (Minutes)',halfsize=halfsize)
            pdf.write(10, 'Unable to create Time Probes Were Within Specified Temperatures table.\n\n')
            # Printing to the console
            print('Unable to create Time Probes Were Within Specified Temperatures table.\n')


    ####################################
    # Delta temperature from setpoints #
    ####################################

    def deltaFromSetpoints(halfsize=False):

        # If there were no probes used, then just create a header and say that there were no probes used
        if len(probe_tagids) == 0:
            sf.writeHeader(pdf, 'Delta Temperature From Setpoints (Setpoint - Actual Value)',halfsize=halfsize)
            pdf.write(10, 'No probes were used during this run.\n\n')
            
        # Otherwise, make the plots and tables
        else:

            try:
                # Getting a list of endspots if it does not currently exist
                getEndspots()

                # Checking the temperature of each thermocouple at setpoint times, and determining difference between setpoint and actual temps
                deltas = []
                for k in range(len(endspots)):
                    array = [str(k+1)]
                    
                    for j in range(len(probedata)):
                        deltatemp = round(tempmultiplier*probedata[j][endspots[k]][1] - currentsetpointlist[k+1][1],1)
                        array.append(deltatemp)

                    deltas.append(array)

                # For each step, inserting the setpoint temperature at the beginning of the corresponding element in deltas
                for k in range(len(deltas)):
                    deltas[k].insert(1,currentsetpointlist[k+1][1])
                    
                    # Then, inserting whether the setpoint went up, down, or held constant since the last setpoint
                    # For the first step, just say it went up
                    if k == 0:
                        deltas[k].insert(2,'Up')
                    else:
                        if currentsetpointlist[k+1][1] > currentsetpointlist[k][1]:
                            deltas[k].insert(2,'Up')
                        elif currentsetpointlist[k+1][1] < currentsetpointlist[k][1]:
                            deltas[k].insert(2,'Down')
                        else:
                            deltas[k].insert(2,'Hold')
                

                # Creating a list of times at the end of each setpoint step
                setpointtimes = []
                for element in endspots:
                    setpointtimes.append(settimes[element-5])

                # Creating a list with delta temperature values for each thermocouple
                dfindex = []
                for k in range(len(deltas)):
                    dfindex.append('Step ' + str(k+1))

                # Plotting delta temperature values (scatter plot)
                fig, ax1 = plt.subplots(figsize=(10,6))

                ax1.grid(linestyle='--', linewidth=1)
                ax1.xaxis.set_minor_locator(minorLocator)
                # Set grid to use minor tick locations. 
                ax1.grid(which = 'minor', linestyle=':')
                labels = []
                for k in range(3,len(deltas[1])):

                    # Determining the label from probe_tagids
                    label = probe_tagids[k-3]["name"]
                    labels.append(label)
                    ax1.scatter(setpointtimes,[x[k] for x in deltas],label = label)

                ax1.set_ylabel('Temperature Difference (C)', fontsize=font_size)
                ax1.set_xlabel('Time Elapsed (Hours)',fontsize=font_size)
                startx, endx = ax1.get_xlim()
                ax1.xaxis.set_ticks(np.arange(0, endx, xticks))
                ax1.yaxis.set_major_locator(MultipleLocator(25))

                ax2 = ax1.twiny()
                ax2.set_xlim(ax1.get_xlim())
                ax2.set_xticks(setpointtimes)
                ax2.set_xticklabels(dfindex,rotation=90)

                # Shrink current axis's height by 10% on the bottom
                box = ax1.get_position()
                ax1.set_position([box.x0, box.y0 + box.height * 0.1,
                                box.width, box.height * 0.9])

                # Put a legend below current axis
                legend = ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15),
                        fancybox=True, shadow=True, ncol=5)

                plt.savefig(filepath + 'deltascatter' + iteration + '.png',bbox_inches='tight')
                ax1.cla()
                ax2.cla()
                ax2.remove()
                plt.cla()
                legend.remove()

                # Add plot to PDF
                sf.addPlot(pdf, 'Delta Temperature From Setpoints (Setpoint - Actual Value)',filepath + 'deltascatter' + iteration + '.png',width=170, halfsize=halfsize)

                # Add table to PDF
                sf.writeHeader(pdf, 'Delta Temperature From Setpoints (Setpoint - Actual Value)')
                columnnames = ['Step','Temp','Type'] + labels

                # Setting a fill color and font size for the table
                fillColor('light blue')
                pdf.set_font('Helvetica', 'b', 7)

                # Determining where the top of the table is going to be
                pdf.ln(8)
                top = pdf.get_y()
                linelocations = [pdf.get_x()]

                # Writing the column names
                for k in range(len(columnnames)):
                    pdf.cell(9, 5, columnnames[k], border=1, fill=True)

                    # Getting the x location of some cells so that thicker lines can be drawn in some areas
                    if k == 2 or k == 5 or k == 20:
                        linelocations.append(pdf.get_x())

                # Now making a row for each step
                for k in range(len(deltas)):

                    # Determining the index of the min and max delta temperature values for P1-P15
                    minindex = deltas[k].index(min(deltas[k][6:]))
                    maxindex = deltas[k].index(max(deltas[k][6:]))

                    # Setting location of row
                    pdf.set_xy(pdf.l_margin,pdf.get_y()+5)

                    # Setting the fill colors to be lightly gray if the setpoint is holding constant
                    if deltas[k][2] == 'Hold':
                        for j in range(len(deltas[k])):

                            if j == 0:
                                fillColor('light blue')
                                pdf.set_font('Helvetica', 'b', 7)
                                pdf.cell(9, 5, str(deltas[k][j]), border=1, fill=True)
                                pdf.set_font('Helvetica', '', 7)

                            elif j == minindex:
                                fillColor('gray orange', pdf=pdf)
                                pdf.cell(9, 5, str(deltas[k][j]), border=1, fill=True)

                            elif j == maxindex:
                                fillColor('gray')
                                pdf.cell(9, 5, str(deltas[k][j]), border=1, fill=True)

                            else:
                                fillColor('light gray')
                                pdf.cell(9, 5, str(deltas[k][j]), border=1, fill=True)

                    # If setpoint temp is going up or down, colors will not be grayed out
                    else:
                        for j in range(len(deltas[k])):

                            if j == 0:
                                fillColor('light blue')
                                pdf.set_font('Helvetica','b',7)
                                pdf.cell(9, 5, str(deltas[k][j]), border=1, fill=True)
                                pdf.set_font('Helvetica','',7)

                            elif j == minindex:
                                fillColor('light orange')
                                pdf.cell(9, 5, str(deltas[k][j]), border=1, fill=True)

                            elif j == maxindex:
                                fillColor('gray')
                                pdf.cell(9, 5, str(deltas[k][j]), border=1, fill=True)

                            else:
                                pdf.cell(9, 5, str(deltas[k][j]), border=1, fill=False)

                # Drawing thicker lines in some areas
                bottom = pdf.get_y() + 5
                pdf.set_draw_color(0, 0, 0)
                pdf.set_line_width(0.5)

                for location in linelocations:
                    pdf.line(location, top, location, bottom)

                # Drawing line at the top and bottom of the table
                pdf.line(linelocations[0], top, linelocations[-1], top)
                pdf.line(linelocations[0], bottom, linelocations[-1], bottom)

                # Setting the line width back to normal
                pdf.set_line_width(0.2)

                # Setting the font size back to what it was
                pdf.set_font('Helvetica', '', font_size)

            except:
                # Printing to the PDF that there was an error
                sf.writeHeader(pdf,'Delta Temperature From Setpoints (Setpoint - Actual Value)',halfsize=halfsize)
                pdf.write(10, 'Unable to create Delta Temperature From Setpoints table.\n\n')
                # Printing to the console
                print('Unable to create Delta Temperature From Setpoints table.\n')


    ####################################
    # Delta temperature between blocks #
    ####################################

    def deltaBetweenBlocks(halfsize=False, xadjust=0, yadjust=0):

        try:
            # Getting delta temp values between blocks
            getBlockDeltas()

            # Plotting delta temperature values between blocks
            fig, ax1 = sf.createPlot(x=[blockdeltatimeselapsed[:len(blockdeltatemps)],settimes[:len(settemps)]], y=[blockdeltatemps[:len(blockdeltatimeselapsed)],settemps[:len(settimes)]],
                                    labels=['Block Delta Temperatures','Setpoint Temperatures'], xlabel='Time Elapsed (Hours)', ylabel='Temperature (C)')

            # Set grid to use minor tick locations. 
            ax1.grid(which = 'minor', linestyle=':')
            legend = fig.legend(loc='upper center', bbox_to_anchor=(0.5, 0.0),
                    fancybox=True, shadow=True, ncol=2)

            plt.savefig(filepath + 'blockdeltas' + iteration + '.png',bbox_inches='tight')
            ax1.clear()
            plt.cla()
            legend.remove()

            # Add plot to PDF
            sf.addPlot(pdf, 'Delta Temperature Between Blocks',filepath + 'blockdeltas' + iteration + '.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust)

        except:
            # Printing to the PDF that there was an error
            sf.writeHeader(pdf,'Delta Temperature Between Blocks',halfsize=halfsize)
            pdf.write(10, 'Unable to create Delta Temperature Between Blocks plot.\n\n')
            # Printing to the console
            print('Unable to create Delta Temperature Between Blocks plot.\n')


    ###############################
    # Furnace pressure and vacuum #
    ###############################

    def pressureAndVacuum(halfsize=False, xadjust=0, yadjust=0):

        try:
            # Plotting furnace pressure and vacuum
            fig, ax1 = sf.createPlot(x=[pressuretime], y=[pressure], labels=['Pressure'], xlabel='Time Elapsed (Hours)', ylabel='Pressure (mbar)', fixticks=False)

            # Set grid to use minor tick locations. 
            ax1.grid(which = 'minor', linestyle=':')
            plt.yscale("log")
            startx, endx = ax1.get_xlim()
            ax1.xaxis.set_ticks(np.arange(0, endx, xticks))

            # Second axis created for plotting vacuum levels
            ax2 = ax1.twinx()
            ax2.plot(vacuumtime,vacuum, color='k', label = 'Vacuum')
            plt.yscale("log")
            ax2.set_ylabel('Vacuum (mbar)',fontsize=font_size)
            
            
            # Third axis created for plotting furnace temperature
            ax3 = ax1.twinx()
            ax3.spines["right"].set_position(("axes", 1.1))
            # If the average furnace temperature is available, then plot it. Otherwise plot furnace TC temperature
            # if len(tempsf) > 0:
            #     ax3.plot(tempsftimeselapsed,avgftemps, color = 'r',label = 'Average Furnace Temperature')
            # else:
            ax3.plot(furnacetemperaturetime,furnacetemperature, color = 'r',label = 'Furnace TC Temperature')
            ax3.set_ylabel('Furnace Temperature (C)',fontsize=font_size)

            legend = fig.legend(loc='upper center', bbox_to_anchor=(0.5, 0),
                                fancybox=True, shadow=True, ncol=5)
            
            plt.savefig(filepath + 'pressureandvacuum' + iteration + '.png',bbox_inches='tight')
            ax1.clear()
            ax2.clear()
            legend.remove()

            # Add plot to PDF
            sf.addPlot(pdf, 'Furnace Temperature, Pressure, and Vacuum',filepath + 'pressureandvacuum' + iteration + '.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust)

        except:
            # Printing to the PDF that there was an error
            sf.writeHeader(pdf,'Furnace Temperature, Pressure, and Vacuum',halfsize=halfsize)
            pdf.write(10, 'Unable to create Furnace Temperature, Pressure, and Vacuum plot.\n\n')
            # Printing to the console
            print('Unable to create Furnace Temperature, Pressure, and Vacuum plot.\n')


    ###########################################################
    # Furnace temperature, vacuum, and predicted temperatures #
    ###########################################################

    def tempVacPredictions(halfsize=False, xadjust=0, yadjust=0):

        try:
            # Creating average temperature arrays if they have not already been created
            hottestCoolest()

            # Predicting temperature outcomes based on average furnace temperature
            avgprediction, coldprediction, hotprediction = sf.predict(avgftemps)

            # Plotting furnace temperature and vacuum
            fig, ax1 = sf.createPlot(x=[furnacetemperaturetime,furnacetemperaturetime,furnacetemperaturetime,furnacetemperaturetime],
                                    y=[avgftemps,avgprediction,hotprediction,coldprediction], labels=['Average Furnace Temp',
                                    'Predicted Average Block Temp','Predicted Hottest Block Temp','Predicted Coolest Block Temp'], xlabel='Time Elapsed (Hours)', ylabel='Temperature (C)')

            # Set grid to use minor tick locations. 
            ax1.grid(which = 'minor', linestyle=':')

            # Plotting vacuum levels on secondary axis
            ax2 = ax1.twinx()
            ax2.plot(vacuumtime,vacuum, color = 'k',label = 'Vacuum')
            ax2.set_ylabel('Vacuum (mbar)',fontsize=font_size)
            plt.yscale("log")
            legend = fig.legend(loc='upper center', bbox_to_anchor=(0.5, 0),
                    fancybox=True, shadow=True, ncol=3)

            plt.savefig(filepath + 'temperatureandvacuum' + iteration + '.png',bbox_inches='tight')
            ax1.clear()
            ax2.clear()
            legend.remove()

            # Add plot to PDF
            sf.addPlot(pdf, 'Furnace Temperature, Vacuum, and Predicted Material Temps (min, avg, max)',filepath + 'temperatureandvacuum' + iteration + '.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust)

        except:
            # Printing to the PDF that there was an error
            sf.writeHeader(pdf,'Furnace Temperature, Vacuum, and Predicted Material Temps (min, avg, max)',halfsize=halfsize)
            pdf.write(10, 'Unable to create Furnace Temperature, Vacuum, and Predicted Material Temps (min, avg, max) plot.\n\n')
            # Printing to the console
            print('Unable to create Furnace Temperature, Vacuum, and Predicted Material Temps (min, avg, max) plot.\n')


    #################
    # Furnace power #
    #################

    def furnacePower(halfsize=False, xadjust=0, yadjust=0):

        try:
            # Plotting furnace power
            fig, ax1 = sf.createPlot(x=[activepowertime], y=[activepower], labels=['Active Power'],
                                        xlabel='Time Elapsed (Hours)', ylabel='Active Power (kW)', fixticks=False)

            startx, endx = ax1.get_xlim()
            ax1.xaxis.set_ticks(np.arange(0, endx, xticks))

            # Set grid to use minor tick locations. 
            ax1.grid(which = 'minor', linestyle=':')

            # Plotting apparent power on secondary axis
            ax2 = ax1.twinx()
            ax2.plot(apparentpowertime,apparentpower, color = 'b',label = 'Apparent Power')
            ax2.set_ylabel('Apparent Power (kVA)',fontsize=font_size)

            # Plotting energy import on third axis
            ax3 = ax1.twinx()
            ax3.spines["right"].set_position(("axes", 1.1))
            ax3.plot(energyimporttime,energyimport, color = 'r',label = 'Energy Import')
            ax3.set_ylabel('Energy (Wh)',fontsize=font_size)

            legend = fig.legend(loc='upper center', bbox_to_anchor=(0.5, 0),
                    fancybox=True, shadow=True, ncol=4)

            plt.savefig(filepath + 'furnacepower' + iteration + '.png',bbox_inches='tight')
            ax1.clear()
            ax2.clear()
            legend.remove()

            # Add plot to PDF
            sf.addPlot(pdf, 'Furnace Power',filepath + 'furnacepower' + iteration + '.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust)

        except:
            # Printing to the PDF that there was an error
            sf.writeHeader(pdf,'Furnace Power',halfsize=halfsize)
            pdf.write(10, 'Unable to create Furnace Power plot.\n\n')
            # Printing to the console
            print('Unable to create Furnace Power plot.\n')


    ##################
    # Furnace energy #
    ##################

    def furnaceEnergy(halfsize=False, xadjust=0, yadjust=0):

        try:
            # Creating average temperature arrays
            hottestCoolest()

            # Plotting furnace energy and temperature
            fig, ax1 = sf.createPlot(x=[energyimporttime], y=[energyimport], 
                                    labels=['Energy Import'], xlabel='Time Elapsed (Hours)', ylabel='Energy (Wh)', fixticks=False)

            # Set grid to use minor tick locations. 
            ax1.grid(which = 'minor', linestyle=':')
            startx, endx = ax1.get_xlim()
            ax1.xaxis.set_ticks(np.arange(0, endx, xticks))

            # Plotting furnace temperatures on secondary axis
            ax2 = ax1.twinx()
            # if len(tempsf) > 0:
            #     ax2.plot(tempsftimeselapsed,avgftemps, color = 'r',label = 'Average Furnace Temperature')
            # else:
            ax2.plot(furnacetemperaturetime,furnacetemperature, color = 'r',label = 'Furnace TC Temperature')
            ax2.set_ylabel('Temperature (C)',fontsize=font_size)
            legend = fig.legend(loc='upper center', bbox_to_anchor=(0.5, 0),
                    fancybox=True, shadow=True, ncol=4)

            start, end = ax2.get_ylim()
            ax2.yaxis.set_ticks(np.arange(0, end, 100))

            plt.savefig(filepath + 'furnaceenergy' + iteration + '.png',bbox_inches='tight')
            ax1.clear()
            ax2.clear()
            plt.cla()
            legend.remove()

            # Add plot to PDF
            sf.addPlot(pdf, 'Energy used during the run: {} kWh'.format(energyused),filepath + 'furnaceenergy' + iteration + '.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust)

        except:
            # Printing to the PDF that there was an error
            sf.writeHeader(pdf,'Furnace Energy',halfsize=halfsize)
            pdf.write(10, 'Unable to create Furnace Energy plot.\n\n')
            # Printing to the console
            print('Unable to create Furnace Energy plot.\n')


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
            ax1.plot([(x[2] - starttime)/3600000 for x in attributes[24]],[x[1] for x in attributes[24]],color='blue',label = 'Temperature')
            ax2.plot([(x[2] - starttime)/3600000 for x in attributes[25]],[x[1] for x in attributes[25]],color='black',label = 'Relative Humidity')
            ax3.plot([(x[2] - starttime)/3600000 for x in attributes[26]],[x[1] for x in attributes[26]],color='red',label = 'Barometric Pressure')

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
            pdf.cell(40, 6, datetime.datetime.fromtimestamp(attributes[24][0][2]/1000).strftime('%Y-%m-%d %H:%M:%S'), 1, 0, 'C')
            pdf.cell(40, 6, str(round(attributes[24][0][1],2)), 1, 0, 'C')
            pdf.cell(40, 6, str(round(attributes[25][0][1],2)), 1, 0, 'C')
            pdf.cell(40, 6, str(round(attributes[26][0][1],2)), 1, 1, 'C')

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
            ax1.plot([(x[2] - starttime)/3600000 for x in attributes[27]],[x[1] for x in attributes[27]],color='blue',label = 'Temperature')
            ax2.plot([(x[2] - starttime)/3600000 for x in attributes[28]],[x[1] for x in attributes[28]],color='black',label = 'Relative Humidity')

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
            pdf.cell(40, 6, datetime.datetime.fromtimestamp(attributes[27][0][2]/1000).strftime('%Y-%m-%d %H:%M:%S'), 1, 0, 'C')
            pdf.cell(40, 6, str(round(attributes[27][0][1],2)), 1, 0, 'C')
            pdf.cell(40, 6, str(round(attributes[28][0][1],2)), 1, 1, 'C')

            # Adding plot to the PDF
            sf.addPlot(pdf, 'Indoor Weather Station', filepath + 'indoorWeather.png', halfsize=halfsize, xadjust=xadjust, yadjust=yadjust, header=False)

        except:
            # Printing to the PDF that there was an error
            pdf.write(10, 'Unable to create Indoor Weather Station plot.\n\n')
            # Printing to the console
            print('Unable to create Indoor Weather Station plot.\n')


    ##############
    # Parameters #
    ##############

    def getParameters(halfsize=False):

        # Creating the parameter header
        sf.paramHeader(pdf)

        # Writing in all parameters from current and previous run
        try:
            sf.writeParameters(pdf, parametervalues)
        except:
            # Printing to the PDF that there was an error
            sf.writeHeader(pdf,'Parameters',halfsize=halfsize)
            pdf.write(10, 'Unable to find parameters used for the run\n\n')
            # Printing to the console
            print('Unable to find parameters used for the run.\n')


    ##############################################
    # Hottest, coolest, and average temperatures #
    ##############################################

    def hottestCoolest():
        # Finding the hottest and coolest blocks, and average temperature of all blocks
        # Also finding the delta temperature between hottest and coldest blocks
        
        global hottest
        global coolest
        global averagetemp
        global avgftemps

        hottest = []
        coolest = []
        averagetemp = []
        avgftemps = []


        try:
            for i in range(maxlength):
                temps = []
                for probe in probedata:
                    temperature = tempmultiplier*probe[i][1]
                    temps.append(temperature)
                hottemp = max(temps)
                coldtemp = min(temps)
                tempsum = sum(temps)
                
                hottest.append(hottemp)
                coolest.append(coldtemp)
                averagetemp.append(tempsum / len(temps))

            # Finding the average furnace temperature throughout the run
            for k in range(len(tempsf)):
                avgtemp = (tempsf[k] + tempsc[k] + tempsr[k]) / 3
                avgftemps.append(avgtemp)
        except:
            avgftemps = furnacetemperature


    #################
    # Batch Details #
    #################

    def batchDetails(pdf):
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
        pdf.multi_cell(55,5.5,'Output Quantity (HMI)')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(85,5.5,str(runarray[0][5][2]))
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
        pdf.multi_cell(55,5.5,'Power Consumption')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(85,5.5,str(energyused) + ' kWh')
        pdf.multi_cell(55,5.5,'Multiplier Applied?')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        if multiply == True:
            pdf.multi_cell(85,5.5,'Yes')
        else:
            pdf.multi_cell(85,5.5,'No')


    #############################
    # Report creating functions #
    #############################

    # Making a function that creates single reports
    def singleReport(pdf):

        # Creating a new page and header for each report added to this bigger report
        # Add main title
        pdf.add_page()
        pdf.set_font('Helvetica', 'b', 20)  
        pdf.ln(5)
        pdf.write(5, 'Sintering Furnace Report')
        pdf.ln(10)
        
        # Add date of report
        pdf.set_font('Helvetica', 'b', 14)

        pdf.write(5,'Batch Details')
        pdf.ln(1)
        pdf.write(5,sf.underline)
        pdf.ln(10)

        # Adding in the batch details
        pdf.set_font('Helvetica', '', 10)
        pdf.multi_cell(55,5.5,'Batch ID')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(85,5.5,runarray[3])
        pdf.multi_cell(55,5.5,'Product ID')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(85,5.5,str(runarray[4]) + ' (' + sf.productType(runarray[4]) + ')')
        pdf.multi_cell(55,5.5,'Output Quantity (Dashboard)')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(85,5.5,runarray[5][0])
        pdf.multi_cell(55,5.5,'Output Quantity (Transfer Bottles)')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(85,5.5,runarray[5][1])
        pdf.multi_cell(55,5.5,'Output Quantity (SCADA)')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(85,5.5,str(runarray[5][2]))
        pdf.multi_cell(55,5.5,'Operator ID')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(85,5.5,runarray[8])
        pdf.multi_cell(55,5.5,'Description')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(135,5.5,runarray[7])
        pdf.multi_cell(55,5.5,'Equipment')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(105,5.5,runarray[9] + ' (ID: ' + runarray[2] + ')')
        pdf.multi_cell(55,5.5,'Date')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(105,5.5,str(runarray[6]))
        pdf.multi_cell(55,5.5,'Total Run Time')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(85,5.5,str(totalruntime))
        pdf.multi_cell(55,5.5,'Power Consumption')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(85,5.5,str(energyused) + ' kWh')
        pdf.multi_cell(55,5.5,'Multiplier Applied?')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        if multiply == True:
            pdf.multi_cell(85,5.5,'Yes')
        else:
            pdf.multi_cell(85,5.5,'No')


        pdf.add_page()

        setpointTemperatures()
        actualTemperature()
        setpointVActualTemperatures()

        rpmDuringCooling()
        pressureWhileCooling()
        rampRates()
        pressureAndVacuum()

        furnacePower()
        furnaceEnergy()
        getParameters()

        # Creating a page with all Tag ID information
        pdf.add_page()
        sf.writeHeader(pdf, 'Setpoint Tag ID Information')
        sf.makeTable(pdf, ['Step     Number','Setpoint Temp Tag ID','Setpoint Time Tag ID'],setpointtags,datawidth=28,titlewrap=1)
        sf.writeHeader(pdf, 'Other Tag IDs')
        sf.makeTable(pdf, ['Name','Tag ID'],[list(name.values()) for name in attributes_tagids],labelwidth=50)

        # Closing all figures so that they don't stay open and take up too much memory if function is called multiple times
        plt.close('all')


    # Making a function that creates full reports with every section included
    def fullReport(pdf):

        # Creating a new page and header for each report added to this bigger report
        # Add main title
        pdf.add_page()
        pdf.set_font('Helvetica', 'b', 20)  
        pdf.ln(5)
        pdf.write(5, 'Sintering Furnace Report Full')
        pdf.ln(10)
        
        # Add date of report
        pdf.set_font('Helvetica', 'b', 14)

        pdf.write(5,'Batch Details')
        pdf.ln(1)
        pdf.write(5,sf.underline)
        pdf.ln(10)

        # Adding in the batch details
        pdf.set_font('Helvetica', '', 10)
        pdf.multi_cell(55,5.5,'Batch ID')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(85,5.5,runarray[3])
        pdf.multi_cell(55,5.5,'Product ID')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(85,5.5,str(runarray[4]) + ' (' + sf.productType(runarray[4]) + ')')
        pdf.multi_cell(55,5.5,'Output Quantity (Dashboard)')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(85,5.5,runarray[5][0])
        pdf.multi_cell(55,5.5,'Output Quantity (Transfer Bottles)')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(85,5.5,runarray[5][1])
        pdf.multi_cell(55,5.5,'Output Quantity (HMI)')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(85,5.5,str(runarray[5][2]))
        pdf.multi_cell(55,5.5,'Operator ID')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(85,5.5,runarray[8])
        pdf.multi_cell(55,5.5,'Description')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(135,5.5,runarray[7])
        pdf.multi_cell(55,5.5,'Equipment')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(105,5.5,runarray[9] + ' (ID: ' + runarray[2] + ')')
        pdf.multi_cell(55,5.5,'Date')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(105,5.5,str(runarray[6]))
        pdf.multi_cell(55,5.5,'Total Run Time')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(85,5.5,str(totalruntime))
        pdf.multi_cell(55,5.5,'Power Consumption')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        pdf.multi_cell(85,5.5,str(energyused) + ' kWh')
        pdf.multi_cell(55,5.5,'Multiplier Applied?')
        pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
        if multiply == True:
            pdf.multi_cell(85,5.5,'Yes')
        else:
            pdf.multi_cell(85,5.5,'No')

        # Adding in thermocouple positions
        try:
            tcpositions()
        except:
            print('\nUnable to create TC positions section.') 
            print('Either there were none, or else there were too many listed and none were from the day of the furnace run.\n')
            raise SystemExit()

        pdf.add_page()

        setpointTemperatures()
        actualTemperature()
        setpointVActualTemperatures()
        minMaxDeltaTemps()

        setVActualAbv()
        rpmDuringCooling()
        pressureWhileCooling()
        rampRates()

        timeNearSpecTemps()
        deltaFromSetpoints()
        deltaBetweenBlocks()
        pressureAndVacuum()
        tempVacPredictions()

        furnacePower()
        furnaceEnergy()
        getParameters()

        # Creating a page with all Tag ID information
        pdf.add_page()
        sf.writeHeader(pdf, 'Setpoint Tag ID Information')
        sf.makeTable(pdf, ['Step     Number','Setpoint Temp Tag ID','Setpoint Time Tag ID'],setpointtags,datawidth=28,titlewrap=1)
        sf.writeHeader(pdf, 'Other Tag IDs')
        sf.makeTable(pdf, ['Name','Tag ID'],[list(name.values()) for name in attributes_tagids],labelwidth=50)

        # Closing all figures so that they don't stay open and take up too much memory if function is called multiple times
        plt.close('all')

        # Naming the PDF file that was created
        # pdf.output(filepath + '/Report' + reporttype + batchid + '.pdf','F')

        


    # Making a report that is currently used in the traceability reports
    def comprehensiveReport(pdf=pdf, runarray=runarray):

        # Creating a new page and header for each report added to this bigger report
        pdf.add_page()
        pdf.set_font('Helvetica', 'b', 16)  
        pdf.ln(5)
        pdf.write(5, 'Process ' + str(runarray[0][0]) + ' - ' + str(runarray[0][1]))
        pdf.ln(8)

        # Adding in the batch details
        batchDetails(pdf)

        # Adding in the sections to be used
        # Sometimes, x and y values are specified so that plots can be placed next to each other
        setpointTemperatures(halfsize=True)

        ybefore = pdf.get_y()
        setpointVActualTemperatures(halfsize=True)

        if ybefore < 200:
            pdf.set_y(ybefore)
        else:
            pdf.set_y(10)

        rpmDuringCooling(halfsize=True,xadjust=90)

        ybefore = pdf.get_y()
        pressureWhileCooling(halfsize=True)

        if ybefore < 200:
            pdf.set_y(ybefore)
        else:
            pdf.set_y(10)
            
        pressureAndVacuum(halfsize=True,xadjust=90)

        ybefore = pdf.get_y()
        furnacePower(halfsize=True)

        if ybefore < 200:
            pdf.set_y(ybefore)
        else:
            pdf.set_y(10)
        furnaceEnergy(halfsize=True,xadjust=90)

        pdf.add_page()
        indoorWeatherStation(pdf=pdf, halfsize=True)
        outdoorWeatherStation(pdf=pdf, halfsize=True)

        # Adding in the run parameters
        try:
            sf.runParameters(pdf, runarray[1][60:])
        except:
            # Print onto the pdf that there were no run parameters found
            pdf.set_font('Helvetica', 'b', 12)
            pdf.ln(5)
            pdf.write(5, 'No run parameters found')

        # Adding in the list of tag IDs that were used to gather data
        try:
            sf.addTags(attributes_tagids, pdf=pdf)
        except:
            # Print onto the pdf that there were no tags found
            pdf.set_font('Helvetica', 'b', 12)
            pdf.ln(5)
            pdf.write(5, 'No tags found')

        # Closing all figures so that they don't stay open and take up too much memory if function is called multiple times
        plt.close('all')


    # Adding sections to the PDF for customer report
    def customerReport(pdf):

        # Creating a header for each equipment report added to the larger customer report
        pdf.set_font('Helvetica', 'b', 16)
        pdf.ln(5)
        pdf.write(5, 'Process ' + str(runarray[0][0]) + ' - ' + str(runarray[0][1]))
        pdf.ln(8)

        # Adding in batch details
        batchDetails(pdf)

        # Adding in some space at the end
        pdf.ln(10)


    # Specifying which type of report is to be made
    if reporttype == 'full':
        fullReport(pdf)
    elif reporttype == 'single':
        singleReport(pdf)
    elif reporttype == 'comprehensive':
        comprehensiveReport(pdf)
    elif reporttype == 'customer':
        customerReport(pdf)