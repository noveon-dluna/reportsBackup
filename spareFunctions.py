# This contains various functions that may be useful in multiple scripts

#################################
# Importing Necessary Libraries #
#################################

import datetime
from joblib import load
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import math
import pymysql


#######################################
# Establishing connection to database #
#######################################

# Connection to SCADA
host = "dbs.corp.urbanminingco.com"
user = "readonly"
passwd = "!0n1yR34d!"
db = "SCADA"
db = pymysql.connect(host=host, user=user, passwd=passwd, db=db)
cur = db.cursor()

# Connection to UMCDB
umcdb = "UMCDB"
umcdb = pymysql.connect(host=host, user=user, passwd=passwd, db=umcdb)
umccur = umcdb.cursor()


################################
# Loading in prediction models #
################################

filepath = 'C:/Users/dluna/Desktop/pythonProjects/sfReports/predictionModels/'

backwardsearlymodel = load(filepath + 'backwardsearlymodel.joblib')
backwardslowmodel = load(filepath + 'backwardslowmodel.joblib')
backwardsmediummodel = load(filepath + 'backwardsmediummodel.joblib')
backwardshighmodel = load(filepath + 'backwardshighmodel.joblib')

earlymodel = load(filepath + 'earlymodel.joblib')
lowmodel = load(filepath + 'lowmodel.joblib')
mediummodel = load(filepath + 'mediummodel.joblib')
highmodel = load(filepath + 'highmodel.joblib')

hotearlymodel = load(filepath + 'hotearlymodel.joblib')
hotlowmodel = load(filepath + 'hotlowmodel.joblib')
hotmediummodel = load(filepath + 'hotmediummodel.joblib')
hothighmodel = load(filepath + 'hothighmodel.joblib')

coldearlymodel = load(filepath + 'coldearlymodel.joblib')
coldlowmodel = load(filepath + 'coldlowmodel.joblib')
coldmediummodel = load(filepath + 'coldmediummodel.joblib')
coldhighmodel = load(filepath + 'coldhighmodel.joblib')


######################
# Defining Functions #
######################

# get the dates within a range
def getDatesInRange(startdate, enddate):
    delta = datetime.datetime.date(enddate) - datetime.datetime.date(startdate)
    dates = []
    for i in range(delta.days + 1):
        day = startdate + datetime.timedelta(days=i)
        dates.append(day.strftime("%Y%m%d"))
    return dates

# get a timestamp from a date
def getTimeStamp(date):
    timestamp = datetime.datetime.timestamp(date) * 1000
    return timestamp

# display floats with 2 decimals
def twoDecimals(number):
    newnumber = "{:.2f}".format(number)
    return newnumber

# Find the min, max, and range of a list
def minmax(val_list):
    min_val = min(val_list)
    min_loc = val_list.index(min_val)
    max_val = max(val_list)
    max_loc = val_list.index(max_val)
    r = max_val - min_val

    return (r,min_loc,max_loc)

# Expand a list of setpoints into a full data set of temperatures and times every 5 seconds
def expandSetpoints(setpoints,templocation=0,timelocation=1):
    settemps = [20]
    settimes = [0]

    # First putting all set temperatures and times into lists
    for tuple in setpoints:
        try:
            setpoint = [tuple["T"], tuple["t"]]
            temp = setpoint[0]
            time = setpoint[1]
            
        except:
            temp = tuple[templocation]
            time = tuple[timelocation]

        if temp != 0:
            settemps.append(temp)
            settimes.append(time)

    totaltime = sum(settimes)

    # Now making data points going from one setpoint temperature to the next
    alltemps = []
    alltimes = np.arange(0,totaltime,1/12)

    # Converting times from minutes to hours for graphing
    alltimeshours = []
    for element in alltimes:
        hours = element / 60
        alltimeshours.append(hours)

    # Now making the full list of temperatures to match the times
    for k in range(len(settemps)-1):
        steptime = settimes[k+1]
        pointcount = steptime * 12

        if settemps[k] == settemps[k+1]:
            temps = [settemps[k]] * pointcount
        else:
            temps = np.arange(settemps[k],settemps[k+1],(settemps[k+1] - settemps[k])/pointcount).tolist()

        alltemps = alltemps + temps

    # If alltemps has more elements than alltimes, make them the same length
    if len(alltemps) > len(alltimeshours):
        alltemps = alltemps[:len(alltimeshours)]

    return alltimeshours, alltemps

# Use models to predict temperature outcomes
def predict(temps,direction='forward'):
    # Specifying cutoff temperatures for each model
    earlytemp = 200
    lowtemp = 400
    mediumtemp = 850

    hotearlytemp = 250
    hotlowtemp = 550
    hotmediumtemp = 850

    coldearlytemp = 250
    coldlowtemp = 550
    coldmediumtemp = 875

    overlap = 50

    # Populating arrays with start points
    furnacepredictions = [temps[0]]
    avgpredictions = [temps[0]]
    hotpredictions = [temps[0]]
    coldpredictions = [temps[0]]

    # Now making the rest of the predictions
    if direction == 'forward':
        for k in range(1,len(temps)):
            prevtemp = avgpredictions[k-1]
            prevhottemp = hotpredictions[k-1]
            prevcoldtemp = coldpredictions[k-1]
            avginput = [[temps[k] - avgpredictions[k-1]]]
            hotinput1 = [[temps[k] - hotpredictions[k-1]]]
            hotinput2 = [[temps[k] - hotpredictions[k-1],hotpredictions[k-1] - coldpredictions[k-1]]]
            coldinput = [[avgpredictions[k-1] - coldpredictions[k-1],temps[k] - coldpredictions[k-1]]]

            #Prediction model used will be based on what the previous temperature was
            if prevtemp < earlytemp - overlap:
                prediction = earlymodel.predict(avginput)
            elif prevtemp < earlytemp + overlap:
                prediction = (earlymodel.predict(avginput) + lowmodel.predict(avginput)) / 2
            elif prevtemp < lowtemp - overlap:
                prediction = lowmodel.predict(avginput)
            elif prevtemp < lowtemp + overlap:
                prediction = (lowmodel.predict(avginput) + mediummodel.predict(avginput)) / 2
            elif prevtemp < mediumtemp - overlap:
                prediction = mediummodel.predict(avginput)
            elif prevtemp < mediumtemp + overlap:
                prediction = (mediummodel.predict(avginput) + highmodel.predict(avginput)) / 2
            else:
                prediction = highmodel.predict(avginput)

            if prevhottemp < hotearlytemp - overlap:
                hotprediction = hotearlymodel.predict(hotinput1)
            elif prevhottemp < hotearlytemp + overlap:
                hotprediction = (hotearlymodel.predict(hotinput1) + hotlowmodel.predict(hotinput1)) / 2
            elif prevhottemp < hotlowtemp - overlap:
                hotprediction = hotlowmodel.predict(hotinput1)
            elif prevhottemp < hotlowtemp + overlap:
                hotprediction = (hotlowmodel.predict(hotinput1) + hotmediummodel.predict(hotinput2)) / 2
            elif prevhottemp < hotmediumtemp - overlap:
                hotprediction = hotmediummodel.predict(hotinput2)
            elif prevhottemp < hotmediumtemp + overlap:
                hotprediction = (hotmediummodel.predict(hotinput2) + hothighmodel.predict(hotinput2)) / 2
            else:
                hotprediction = hothighmodel.predict(hotinput2)

            if prevcoldtemp < coldearlytemp - overlap:
                coldprediction = coldearlymodel.predict(coldinput)
            elif prevcoldtemp < coldearlytemp + overlap:
                coldprediction = (coldearlymodel.predict(coldinput) + coldlowmodel.predict(coldinput)) / 2
            elif prevcoldtemp < coldlowtemp - overlap:
                coldprediction = coldlowmodel.predict(coldinput)
            elif prevcoldtemp < coldlowtemp + overlap:
                coldprediction = (coldlowmodel.predict(coldinput) + coldmediummodel.predict(coldinput)) / 2
            elif prevcoldtemp < coldmediumtemp - overlap:
                coldprediction = coldmediummodel.predict(coldinput)
            elif prevcoldtemp < coldmediumtemp + overlap:
                coldprediction = (coldmediummodel.predict(coldinput) + coldhighmodel.predict(coldinput)) / 2
            else:
                coldprediction = coldhighmodel.predict(coldinput)

            # Incorporating phase change into prediction of block temperature
            if 735 < prevhottemp < 738:
                newhottemperature = prevhottemp + (hotprediction[0][0] / 3.5)
            else:
                newhottemperature = prevhottemp + hotprediction[0][0]

            if 735 < prevcoldtemp < 738:
                newcoldtemperature = prevcoldtemp + (coldprediction[0][0] / 3.5)
            else:
                newcoldtemperature = prevcoldtemp + coldprediction[0][0]

            coldpredictions.append(newcoldtemperature)
            hotpredictions.append(newhottemperature)

            newtemperature = prevtemp + prediction[0][0]
            avgpredictions.append(newtemperature)

        return avgpredictions, coldpredictions, hotpredictions

            
    else:
        for k in range(1,len(temps)):
            prevtemp = temps[k-1]

            tempchange = [[temps[k] - temps[k-1]]]

            #Prediction model used will be based on what the previous temperature was
            if prevtemp < earlytemp - overlap:
                prediction = backwardsearlymodel.predict(tempchange)
            elif prevtemp < earlytemp + overlap:
                prediction = (backwardsearlymodel.predict(tempchange) + backwardslowmodel.predict(tempchange)) / 2
            elif prevtemp < lowtemp - overlap:
                prediction = backwardslowmodel.predict(tempchange)
            elif prevtemp < lowtemp + overlap:
                prediction = (backwardslowmodel.predict(tempchange) + backwardsmediummodel.predict(tempchange)) / 2
            elif prevtemp < mediumtemp - overlap:
                prediction = backwardsmediummodel.predict(tempchange)
            elif prevtemp < mediumtemp + overlap:
                prediction = (backwardsmediummodel.predict(tempchange) + backwardshighmodel.predict(tempchange)) / 2
            else:
                prediction = backwardshighmodel.predict(tempchange)

            newtemperature = temps[k] + prediction[0][0]
            furnacepredictions.append(newtemperature)

        return furnacepredictions

# Determining all transfer bottles used for this batch
def transferBottles(batchid, pdf, writetopdf=True, received=False):

    # Defining a function that removes any repeated transfer bottles that shouldn't be there
    def removeTBRepeats(fulltbs):
        # Removing duplicates from fulltbs
        # If there are multiple entries in fulltbs that have the same transfer_bottle_id,
        # Then only use the entry with that bottle with the earliest date.
        # However, if there is an entry with a net weight less than 1, then use the bottle after that as well
        reducedtbs = []
        alreadyused = []
        for bottle in fulltbs:

            # If this bottle ID has not already been used, then it can be added to the reduced list
            if bottle[0] not in alreadyused:

                # Finding all instances when the same bottle ID is used
                samebottles = [x for x in fulltbs if x[0] == bottle[0]]

                # Sort samebottles by date
                samebottles.sort(key=lambda x: x[4])

                # The earliest bottle will always be used regardless, as long as its net weight is > 1
                if (samebottles[0][3] - samebottles[0][2]) >= 1:
                    reducedtbs.append(samebottles[0])

                # If this same bottle ID appears multiple times:
                if len(samebottles) > 1:

                    # If there are instances where the total_weight - tare_weight < 1, 
                    # then only use every instance of the bottle that happens immediately after the near 0 value, 
                    # as long as it isn't also a near 0 value
                    if len([y for y in samebottles if ((y[3]-y[2])<1)]) > 0:
                        for k in range(1,len(samebottles)):
                            if (samebottles[k-1][3] - samebottles[k-1][2]) < 1 and (samebottles[k][3] - samebottles[k][2]) > 1:
                                reducedtbs.append(samebottles[k])

                # Adding this bottle ID to the alreadyused list
                alreadyused.append(bottle[0])

        # Returning the reduced list of transfer bottles
        return reducedtbs

    # Transfer bottles out
    # Finding entries in SCADA.eq_transfer_bottles_status that have the same batch ID (transfer bottles out)
    cur.execute("SELECT a.transfer_bottle_id, a.content_type, a.tare_weight, a.total_weight, a.time_filled, a.time_emptied,\
                b.nvn_eq_id, b.content_assignment\
                FROM eq_transfer_bottles_status a INNER JOIN eq_transfer_bottles b\
                ON a.transfer_bottle_id=b.id\
                WHERE a.batch_id='{}' ORDER BY b.id".format(batchid))
    fulltransferbottlesout = makeArray(cur.fetchall())

    # Removing any repeated transfer bottle listings that should not be there
    transferbottlesout = removeTBRepeats(fulltransferbottlesout)
    

    # Calculating the total weight out for each transfer bottle
    netweightsout = []
    for element in transferbottlesout:
        netweight = float(twoDecimals(element[3] - element[2]))
        netweightsout.append(netweight)
        element.append(netweight)
    totalweightout = twoDecimals(sum(netweightsout))


    # Transfer bottles in
    if received == False:

        # Finding the component batch ID from the batch ID
        try:
            umccur.execute("SELECT component_batch_id FROM batch_inputs WHERE batch_id = '{}'".format(batchid))
            componentbatchid = umccur.fetchall()[0][0]
        except:
            componentbatchid = 'None'

        # Finding entries from the same table for the component batch ID (transfer bottles in)
        cur.execute("SELECT a.transfer_bottle_id, a.content_type, a.tare_weight, a.total_weight, a.time_filled, a.time_emptied,\
                    b.nvn_eq_id, b.content_assignment\
                    FROM eq_transfer_bottles_status a INNER JOIN eq_transfer_bottles b\
                    ON a.transfer_bottle_id=b.id\
                    WHERE a.batch_id='{}' ORDER BY b.id".format(componentbatchid))
        fulltransferbottlesin = makeArray(cur.fetchall())

        # Removing any repeated transfer bottle listings that should not be there
        transferbottlesin = removeTBRepeats(fulltransferbottlesin)
        

        # Calculating the total weight in for each transfer bottle
        netweightsin = []
        for element in transferbottlesin:
            netweight = float(twoDecimals(element[3] - element[2]))
            netweightsin.append(netweight)
            element.append(netweight)
        totalweightin = twoDecimals(sum(netweightsin))

    

    # Writing the transfer bottle information to the PDF
    if writetopdf == True and received == False:

        # Creating a header for the transfer bottles section
        top = pdf.get_y()
        writeHeader(pdf, 'Transfer Bottles In: {}'.format(componentbatchid), halfsize=True)
        pdf.set_xy(pdf.l_margin,top)
        writeHeader(pdf, 'Transfer Bottles Out: {}'.format(batchid), halfsize=True, xadjust=90)
        top = pdf.get_y()

        # Writing all of the transfer bottle in information to the PDF
        pdf.set_font('Helvetica', '', 10)
        for element in transferbottlesin:
            pdf.set_xy(pdf.l_margin,pdf.get_y()+5)
            pdf.cell(80, 5, '{}   Net Wt: {} kg\n'.format(element[6],element[8]))

        # Determining the bottom of the transfer bottles in section
        bottomin = pdf.get_y()
        
        # Writing all of the transfer bottle out information to the PDF
        pdf.set_xy(pdf.l_margin+80,top)
        for element in transferbottlesout:
            pdf.set_xy(pdf.l_margin+90,pdf.get_y()+5)
            pdf.cell(80, 5, '{}   Net Wt: {} kg\n'.format(element[6],element[8]))

        # Determining the bottom of the transfer bottles out section
        bottomout = pdf.get_y()

        # Setting the y position to either bottomin or bottomout, whichever is lower on the page
        pdf.set_xy(pdf.l_margin, max(bottomin,bottomout))

        # Writing the total weight in and out to the PDF
        pdf.set_font('Helvetica', 'b', 10)
        pdf.set_xy(pdf.l_margin,pdf.get_y()+10)
        pdf.cell(80, 5, 'Total Weight In: {} kg\n\n'.format(totalweightin))
        pdf.set_xy(pdf.l_margin+90,pdf.get_y())
        pdf.cell(80, 5, 'Total Weight Out: {} kg\n\n'.format(totalweightout))
        pdf.set_font('Helvetica', '', 10)

    elif writetopdf == True and received == True:

        # Creating a header for the transfer bottles section
        writeHeader(pdf, 'Transfer Bottles: {}'.format(batchid), halfsize=True)

        # Writing all of the transfer bottle out information to the PDF
        pdf.set_font('Helvetica', '', 10)
        for element in transferbottlesout:
            pdf.set_xy(pdf.l_margin,pdf.get_y()+5)
            pdf.cell(80, 5, '{}   Net Wt: {} kg\n'.format(element[6],element[8]))

        # Writing the total weight to the PDF
        pdf.set_font('Helvetica', 'b', 10)
        pdf.set_xy(pdf.l_margin,pdf.get_y()+10)
        pdf.cell(80, 5, 'Total Weight: {} kg\n\n'.format(totalweightout))


    # If writetopdf is false, then just return the total weight in and out
    elif writetopdf == False:
        return totalweightin, totalweightout

# Turn SQL query results into array
def makeArray(results,removeNone = False):
    array = []

    if removeNone == False:
        for row in results:
            subarray = []
            for element in row:
                subarray.append(element)
            array.append(subarray)

    else:
        for row in results:
            subarray = []
            for element in row:
                if element is not None:
                    subarray.append(element)
            array.append(subarray)

    return array

# Create a plot
def createPlot(x, y, labels=[''], size=(10,6), xlabel='', ylabel='', font_size=16, fixticks=True):
    fig, ax1 = plt.subplots(figsize=size)
    ax1.grid(linestyle='--', linewidth=1)

    minorLocator = MultipleLocator(1)
    ax1.xaxis.set_minor_locator(minorLocator)

    if len(labels) == len(x):
        for k in range(len(x)):
            ax1.plot(x[k], y[k], label = labels[k])
    else:
        for k in range(len(x)):
            ax1.plot(x[k], y[k])

    ax1.set_xlabel(xlabel, fontsize=font_size)
    ax1.set_ylabel(ylabel, fontsize=font_size)

    if fixticks == True:
        starty, endy = ax1.get_ylim()
        ax1.yaxis.set_ticks(np.arange(0, endy, 100))
        startx, endx = ax1.get_xlim()
        ax1.xaxis.set_ticks(np.arange(0, endx, 3))

    return fig, ax1



underline = '____________________________________________________________________'
halfunderline = '__________________________________'


# Function that gets all tag IDs used for the same purpose, since some get retired and replaced with new ones
def getAllTags(tagid):

    # First getting the tagpath of the input tagid
    cur.execute("SELECT tagpath FROM sqlth_te WHERE id = {}".format(tagid))
    tagpath = makeArray(cur.fetchall())[0][0]

    # Then searching through the sqlth_te table to find all tagids that have the same tagpath
    cur.execute("SELECT id FROM sqlth_te WHERE tagpath = '{}'".format(tagpath))
    tagids = makeArray(cur.fetchall())

    # Creating a comma separated string of all tagids
    tagidstring = ''
    for element in tagids:
        tagidstring += str(element[0]) + ','

    return tagidstring[:-1]


# Defining a function that creates a title page
def create_title(title, pdf, starttime, coolingtype, energyused, totalruntime, operatorid, batchin, batchout, eqid, mass, multiply):
    
    # Add main title
    pdf.set_font('Helvetica', 'b', 20)  
    pdf.ln(5)
    pdf.write(5, title)
    pdf.ln(10)
    
    # Add date of report
    pdf.set_font('Helvetica', 'b', 14)

    pdf.write(5,'Batch Details')
    pdf.ln(1)
    pdf.write(5,underline)
    pdf.ln(10)
    pdf.set_font('Helvetica', '', 12)

    pdf.set_text_color(r=0,g=0,b=0)
    pdf.multi_cell(55,6.5,'Batch Run Date')
    pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-6.5)
    pdf.multi_cell(85,6.5,str(datetime.datetime.fromtimestamp(starttime/1000)).split(".")[0])
    pdf.multi_cell(55,6.5,'Equipment ID')
    pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-6.5)
    pdf.multi_cell(85,6.5,str(eqid))
    pdf.multi_cell(55,6.5,'Cooling Type')
    pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-6.5)
    pdf.multi_cell(85,6.5,coolingtype)
    pdf.multi_cell(55,6.5,'Power Consumption')
    pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-6.5)
    pdf.multi_cell(105,6.5,str(energyused) + ' kVAh')
    pdf.multi_cell(55,6.5,'Total Run Time')
    pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-6.5)
    pdf.multi_cell(105,6.5,str(totalruntime).split(".")[0])
    pdf.multi_cell(55,6.5,'Operator ID')
    pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-6.5)
    pdf.multi_cell(105,6.5,str(operatorid))
    pdf.multi_cell(55,6.5,'Batch Number In')
    pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-6.5)
    pdf.multi_cell(105,6.5,str(batchin))
    pdf.multi_cell(55,6.5,'Batch Number Out')
    pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-6.5)
    pdf.multi_cell(105,6.5,str(batchout))
    pdf.multi_cell(55,6.5,'Mass')
    pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-6.5)
    pdf.multi_cell(105,6.5,str(mass))
    pdf.multi_cell(55,6.5,'Multiplier')
    pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-6.5)
    pdf.multi_cell(105,6.5,str(multiply))
    pdf.ln(8)

# Defining a function that makes the header for the parameters pages
def paramHeader(pdf,header=['Current','Previous','Tag ID']):

    # Adding a new page if needed
    if pdf.get_y() > 250:
        pdf.add_page()
        pdf.set_xy(pdf.l_margin, 10)
    else:
        pdf.ln(10)

    # Determining a starting point for the header based on header length
    if len(header) == 3:
        startpoint = 85
    else:
        startpoint = 115

    # Writing the first part of the header
    pdf.set_font('Helvetica','b',14)
    y = pdf.get_y()
    pdf.write(5, 'Parameters')

    # Writing in the rest of the header
    pdf.set_x(startpoint + pdf.l_margin)
    for k in range(len(header)):
        pdf.multi_cell(30,5.5,header[k])
        pdf.set_xy(startpoint + 30 + (30*k) + pdf.l_margin, y)
    
    # Adding a line under the header
    pdf.ln(1)
    pdf.write(5, underline)
    pdf.ln(5)

    # Setting the font back to normal
    pdf.set_font('Helvetica','',10)

# Add a header above graphs and tables
def writeHeader(pdf,title,fontsize=14,xadjust=0,yadjust=0,halfsize=False,ignoremaxy=False):

    # Setting a y value cutoff where a new page is created based on the value of halfsize
    if halfsize == False:
        maxy = 150
        line = underline
        pdf.set_font('Helvetica', 'b', fontsize)
    else:
        maxy = 215
        line = halfunderline
        pdf.set_font('Helvetica', 'b', fontsize-2)


    # Determining if a new page needs to be created or not
    # If one page gets created for the left image, another should not be made for the right
    y = pdf.get_y()
    if y >= maxy and ignoremaxy == False:
        pdf.add_page()
        y = 20

    # If this header is being written somewhere in the middle of the page, then add space before it
    if y > 30:
        pdf.ln(12)
    
    # Changing it to use multi_cell instead of writing normally
    pdf.set_xy(xadjust + pdf.l_margin, pdf.get_y()+yadjust)
    pdf.multi_cell(200,4,title)
    pdf.set_x(xadjust + pdf.l_margin)
    pdf.multi_cell(200,2,line)

# Defining a function that adds plots to the PDF
def addPlot(pdf,title,name,xadjust=0,yadjust=0,width=180,height=120,fontsize=14,halfsize=False,header=True):

    # If halfsize plot is called for, then decrease width and height
    if halfsize == True:
        width = width / 2.1
        height = height / 2.1

    # Create a header for the image
    if header == True:
        writeHeader(pdf,title,fontsize,halfsize=halfsize,xadjust=xadjust,yadjust=yadjust)

    y = pdf.get_y()
    # if y > 30 and y < 120:
    #     y = pdf.get_y()
    # if y <= 120:
    #     pdf.image(name,w=width,h=height,x=10 + xadjust, y=y + 4 + yadjust)
    # else:
    pdf.image(name,w=width,h=height,x=10 + xadjust, y=y + 4 + yadjust)

    # Setting the y position in the pdf to be at the bottom of the image that was just inserted
    newy = y + height
    pdf.set_y(newy)
    pdf.set_font('Helvetica','',14)

# Create a table from an array of data
def makeTable(pdf, header, data, labelwidth=28, datawidth=20, toprowheight = 5, cellheight=5, fontsize=11, titlewrap=0, halfsize=False):
    pdf.ln(10)
    startx = 0
    sidebyside = False

    # Setting a fill color for the table
    pdf.set_fill_color(240,248,255)

    # If a half sized table is called for, allow it to be made on the right side of the page if possible
    if halfsize == True:
        fontsize = 8
        xbefore = pdf.get_x()

        # If table will have less than 10 rows, then starting point will be x = 100
        if len(data) < 10:
            sidebyside = False
            if xbefore <= 100:
                startx = 100
            else:
                startx = 0

        # Otherwise, starting point will be x = 90, because table will be broken in half and placed side by side
        else:
            sidebyside = True
            if xbefore <= 90:
                startx = 90
            else:
                startx = 0

    pdf.set_font('Helvetica', 'b', fontsize)

    # If table row will be too low, make a new page
    # If the table can be started on the right side instead of below, then it will be
    ybefore = pdf.get_y()
    if ybefore < 260:
        pdf.set_xy(startx + pdf.l_margin,ybefore)
    else:
        pdf.add_page()
        pdf.set_xy(pdf.l_margin,20)
        ybefore = 20
    
    # First make headers for the tables
    for k in range(len(header)):
        if k == 0:
            pdf.multi_cell(labelwidth, toprowheight, header[k], border=1, fill=True)
            pdf.set_xy(startx + pdf.l_margin + labelwidth, ybefore)
        else:
            pdf.multi_cell(datawidth, toprowheight, header[k], border=1, fill=True)
            pdf.set_xy(startx + pdf.l_margin + labelwidth + k*datawidth, ybefore)

    # If it is possible to fit 2 tables next to each other, then do that if needed (only full size tables)
    ntables = 1
    totalwidth = pdf.get_x()
    if totalwidth < 107 and len(data) > 15 and halfsize == False or sidebyside == True:
        # Setting where the right hand table will start
        if sidebyside == True:
            righttablestart = 155
        else:
            righttablestart = 110
        
        ntables = 2
        pdf.set_xy(righttablestart,ybefore)

        # Making the headers for the right table
        for k in range(len(header)):
            if k == 0:
                pdf.multi_cell(labelwidth, toprowheight, header[k], border=1, fill=True)
                pdf.set_xy(righttablestart + labelwidth,ybefore)
            else:
                pdf.multi_cell(datawidth, toprowheight, header[k], border=1, fill=True)
                pdf.set_xy(righttablestart + labelwidth + k*datawidth, ybefore)

    # Setting the y position below the top cells if text wraps
    if titlewrap == 1:
        pdf.set_y(ybefore + toprowheight)

    # Now populate the table with data if there is just one table
    top1 = pdf.get_y()
    if ntables == 1:

        newy = pdf.get_y() + cellheight

        for k in range(len(data)):
            ybefore = pdf.get_y()
            newy = ybefore + cellheight
            pdf.set_xy(startx + pdf.l_margin,newy)

            # If row is too low on page, create new page
            if newy > 260:
                pdf.add_page()
                pdf.set_xy(startx + pdf.l_margin,20)
                newy = 20
            else:
                pdf.set_xy(startx + pdf.l_margin,newy)

            for j in range(len(data[k])):

                if j == 0:
                    pdf.set_font('Helvetica', 'b', fontsize)
                    pdf.multi_cell(labelwidth, cellheight, str(data[k][j]), border = 1, fill=True)
                    pdf.set_xy(startx + pdf.l_margin + labelwidth,newy)
                else:
                    pdf.set_font('Helvetica', '', fontsize)
                    pdf.multi_cell(datawidth, cellheight, str(data[k][j]), border=1)
                    pdf.set_xy(startx + pdf.l_margin + labelwidth + j*datawidth,newy)
                    
        pdf.set_y(newy + cellheight)
        
    # If there are two tables, populate the left table first, then the right table
    else:
        # Determining the number of rows in each table
        if sidebyside == True:
            leftrows = math.ceil(len(data) / 2)
            lefttablestart = 90
        else:
            leftrows = 15
            lefttablestart = 0

        # Left table
        for k in range(leftrows):
            newy = pdf.get_y() + cellheight
            pdf.set_xy(lefttablestart + pdf.l_margin,newy)

            for j in range(len(data[k])):
                
                if j == 0:
                    pdf.set_font('Helvetica', 'b', fontsize)
                    pdf.multi_cell(labelwidth, cellheight, str(data[k][j]), border=1, fill=True)
                    pdf.set_xy(lefttablestart + pdf.l_margin + labelwidth, newy)
                else:
                    pdf.set_font('Helvetica', '', fontsize)
                    pdf.multi_cell(datawidth, cellheight, str(data[k][j]), border=1)
                    pdf.set_xy(lefttablestart + pdf.l_margin + labelwidth + j*datawidth, newy)

        # Getting y value for end of first table, will set y value to this later if needed
        firstrowy = pdf.get_y() + 5
        pdf.set_xy(righttablestart,top1)

        # Right table
        for k in range(leftrows,len(data)):
            newy = pdf.get_y() + cellheight
            pdf.set_xy(righttablestart, newy)

            for j in range(len(data[k])):

                if j == 0:
                    pdf.set_font('Helvetica', 'b', fontsize)
                    pdf.multi_cell(labelwidth,cellheight,str(data[k][j]), border=1, fill=True)
                    pdf.set_xy(righttablestart + labelwidth,newy)
                else:
                    pdf.set_font('Helvetica', '', fontsize)
                    pdf.multi_cell(datawidth, cellheight, str(data[k][j]), border=1)
                    pdf.set_xy(righttablestart + labelwidth + j*datawidth, newy)

        pdf.set_y(firstrowy)

# Function to write out the machine parameters
def runParameters(pdf, array):

    # Adding a new page if needed
    if pdf.get_y() > 240:
        pdf.add_page()

    # Writing in the parameter header
    paramHeader(pdf,header=['Value','Tag ID'])

    # Setting the font
    pdf.set_font('Helvetica', '', 10)

    # Writing in all of the run parameters
    offset = 0
    pdf.ln(5)
    top = pdf.get_y()
    for k in range(len(array)):

        # If the row is too low on the page, create a new page
        if top + offset > 260:
            pdf.add_page()
            pdf.set_xy(pdf.l_margin,10)
            paramHeader(pdf,header=['Value','Tag ID'])
            pdf.set_font('Helvetica', '', 10)
            top = 30
            offset = 0

        # Writing in the parameter name and value
        pdf.set_xy(pdf.l_margin, top + offset)
        pdf.multi_cell(115,5.5,str(array[k][3]))
        pdf.set_xy(115 + pdf.l_margin, top + offset)
        pdf.multi_cell(35,5.5,str(array[k][2]))
        pdf.set_xy(35 + 115 + pdf.l_margin, top + offset)
        pdf.multi_cell(35,5.5,str(array[k][6]))
        offset += 5.5
    pdf.ln(5)


# This is the parameters function that is used in reportSF, but should probably be changed
# Write out a list of machine parameters
def writeParameters(pdf, parameters):

    # Setting the font
    pdf.set_font('Helvetica', '', 10)

    # Adding in a little space before the parameters
    pdf.ln(5)

    # Writing in all parameters from current and previous run
    for element in parameters:
        ybefore = pdf.get_y()
        
        # Highlighting lines with values that changed from the previous run
        if element[2] == element[3]:
            highlight = False
        elif element[3] == '-':
            highlight = False
        else:
            highlight = True
            pdf.set_fill_color(255,69,0)

        # Printing the parameter name
        pdf.set_xy(pdf.l_margin,ybefore)
        pdf.cell(85.0, 5.5, str(element[1]), fill=highlight)
        pdf.set_xy(85.0 + pdf.l_margin,ybefore)

        # Printing the current parameter value, aligned to the right
        pdf.multi_cell(30.0, 5.5, str(round(element[2],3)), fill=highlight, align='R')
        pdf.set_xy(85.0 + 30.0 + pdf.l_margin,ybefore)

        # Printing the previous parameter value, aligned to the right
        if type(element[3]) == float:
            pdf.multi_cell(30.0, 5.5, str(round(element[3],3)), fill=highlight, align='R')
        else:
            pdf.multi_cell(30.0, 5.5, str(element[3]), fill=highlight, align='R')
        pdf.set_xy(85 + 30 + 30 + pdf.l_margin,ybefore)

        # Printing the tag ID for each parameter, aligned to the right
        pdf.multi_cell(20.0, 5.5, str(element[0]), fill=highlight, align='R')
        
        if ybefore >= 265:
            paramHeader(pdf)
            pdf.ln(5)


# Adding a table with all Tag IDs that were used
def addTags(array, pdf):

    # Writing a header first
    writeHeader(pdf,'Tag IDs Used',halfsize=True)

    # Setting the font and determining location of top of the table, to know where to start second column
    pdf.ln(5)
    pdf.set_font('Helvetica', '', 10)
    top = pdf.get_y()
    
    # Writing the tag ID for each of the entries in the first half of the attributes list
    for k in range(math.ceil(len(array)/2)):

        if pdf.get_y() <= 270:
            ybefore = pdf.get_y()
        else:
            pdf.add_page()
            pdf.set_y(15)
            ybefore = pdf.get_y()
        
        pdf.multi_cell(60,5,array[k]["name"])
        pdf.set_xy(60 + pdf.l_margin, ybefore)
        pdf.multi_cell(25,5,array[k]["tagid"])

        # Writing the tag ID for each of the entries in the second half of the attributes list
        try:
            pdf.set_xy(100, ybefore)
            pdf.multi_cell(60,5,array[k + math.ceil(len(array)/2)]["name"])
            pdf.set_xy(100 + 60 + pdf.l_margin, ybefore)
            pdf.multi_cell(25,5,array[k + math.ceil(len(array)/2)]["tagid"])
        except:
            pdf.set_xy(pdf.l_margin, pdf.get_y() + 15)


# Determining the type from the product ID
def productType(productid):

    # Creating a dictionary of product IDs and their corresponding product types
    productTypes = [{"product type":"UMC Alloy", "ID":"UAL"},
                    {"product type":"UMC Powder", "ID":"UPW"},
                    {"product type":"UMC Sintered Magnet", "ID":"UMS"},
                    {"product type":"UMC Bonded Magnet", "ID":"UMB"},
                    {"product type":"UMC Slurry", "ID":"USL"},
                    {"product type":"UMC Pellet", "ID":"UPL"},
                    {"product type":"UMC Finished Magnet", "ID":"UMF"},
                    {"product type":"UMC Assembly", "ID":"UAS"},
                    {"product type":"UMC Pressed Block", "ID":"UMP"},
                    {"product type":"Feed Stock", "ID":"FS"},
                    {"product type":"Impact Modifier", "ID":"IM"},
                    {"product type":"WEEE Assembly", "ID":"WEE"},
                    {"product type":"Plastic Parts", "ID":"PP"},
                    {"product type":"Steel Parts", "ID":"SP"},
                    {"product type":"Fasteners", "ID":"FT"},
                    {"product type":"Adhesives", "ID":"A"}]
    
    # Finding the product type that corresponds to the product ID based on the first 3 letters of the ID. If no product type is found, return 'Unknown'
    product = 'Unknown Product Type'
    for element in productTypes:
        if element["ID"] == productid[:3] or element["ID"] == productid[:2]:
            product = element["product type"]

    return product
        