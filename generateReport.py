#################################
# Importing Necessary Libraries #
#################################

import matplotlib.pyplot as plt
import spareFunctions as sf
import reportSF as rsf
import reportJM as rjm
import reportHD as rhd
import reportOG as rog
import createBHLoop as bh
import reportSieving as rSieving
import reportRollerMixing as rRM
import sys


#######################################
# Establishing connection to database #
#######################################
 
# Connection to SCADA database
cur = sf.cur
# Connection to UMCDB
umccur = sf.umccur


#################################
# Initializing PDF report stuff #
#################################

pdf = rsf.PDF()


###########################
# Establishing File Paths #
###########################

filepath = 'C:/Users/dluna/Desktop/pythonProjects/sfReports/graphs/'


###############
# User Inputs #
###############

# These are all arguments that get passed in when the script is run in the command line
# An example of how to run this script is:
# python3 comprehensive.py B230028 comprehensive multiply

# # Total arguments
# n = len(sys.argv)

# # Arguments passed
# for i in range(n):
#     print('Argument {}: {}'.format(i+1,sys.argv[i]))

# # Getting the batch ID
# batchid = sys.argv[1]

# # Getting the type of report
# type = sys.argv[2]

# # Getting the multiplier
# if len(sys.argv) > 3:
#     multiply = True
# else:
#     multiply = False


#####################
# Section Functions #
#####################

# Get the previous batch IDs for a given batch ID
def getPrevBatches(batchid):

    # Initialize the batchids array with the given batch ID
    batchids = [[batchid]]
    prevbatch = [batchid]

    # Get the previous batch IDs for the given batch ID, until there are no more previous batch IDs
    while len(prevbatch) > 0:
        umccur.execute("SELECT component_batch_id FROM batch_inputs WHERE batch_id='{}'".format(prevbatch[0]))
        prevbatch = [result[0] for result in umccur.fetchall()]

        # If a previous batch ID exists, then append it to the batchids array
        if len(prevbatch) > 0:
            batchids.append([prevbatch[0]]) ############################################ FIX THIS ############################################

    # If the batch was unable to be traced backwards, then state that
    if len(batchids) == 1:

        print('Batch ID {} was unable to be traced backwards'.format(batchid))

        # If the batch does not exist in the batches table, then state that, and exit the function
        umccur.execute("SELECT * FROM batches WHERE batch_id='{}'".format(batchid))
        if len(umccur.fetchall()) == 0:
            print('Batch ID {} does not exist in the batches table. No report will be made'.format(batchid))
            # Quit the program
            quit()

    print(batchids)
    # Return the batchids array
    return batchids
# Returns batchids

# Get all operators for a given batch
def getOperators(batchid):


    # First getting the operator from the equipment_runs table
    try:
        cur.execute("SELECT DISTINCT employee_id FROM equipment_runs WHERE batch_id='{}'".format(batchid))
        operators = [result[0] for result in cur.fetchall()]
    except:
        operators = []


    # Now getting the employee information from the batches table
    try:
        umccur.execute("SELECT employee_id FROM employees WHERE user_id = \
                    (SELECT DISTINCT user_id FROM batches WHERE batch_id='{}')".format(batchid))
        batchoperators = sf.makeArray(umccur.fetchall())[0]
    except:
        batchoperators = []


    # Getting the user ID from the transfer bottles
    try:
        cur.execute("SELECT DISTINCT created_by FROM eq_transfer_bottles_status WHERE batch_id='{}'".format(batchid))
        tbusers = sf.makeArray(cur.fetchall())

        # Getting the employee ID from the transfer bottles user IDs
        tboperators = []
        for user in tbusers:
            umccur.execute("SELECT employee_id FROM UMCDB.employees WHERE user_id = '{}'".format(user[0]))
            tboperators.append(sf.makeArray(umccur.fetchall())[0][0])
    except:
        tboperators = []


    # Combining the operators from equipment_runs, batches, and transfer bottles with a comma between each
    operators = operators + batchoperators + tboperators
    alloperators = ''
    for i in range(len(operators)):
        if i == 0:
            alloperators += operators[i]
        else:
            alloperators += ', ' + operators[i]


    return alloperators


# Get the recipe for each batch in the batchids array
def getBatchRecipes(batchids):

    # Creating an empty list that will be filled with recipe information for each equipment run
    batchrecipes = []

    # Now every element in batchids needs to have information filled in
    for k in range(len(batchids)):

        # Creating a step number and inserting it at the beginning of each element
        step = len(batchids) - k
        batchids[k].insert(0,step)

        # Getting the operators for each batch ID
        operators = getOperators(batchids[k][1])

        # Getting product_id and quantity from batch_outputs
        umccur.execute("SELECT product_id, quantity, unit FROM batch_outputs WHERE batch_id='{}'".format(batchids[k][1]))
        results = sf.makeArray(umccur.fetchall())

        # Adding the results into the batchids array
        if len(results) > 0:
            batchids[k].append(results[0][0])
            batchids[k].append(str(float(results[0][1])) + ' ' + str(results[0][2]))
        else:
            print('Product ID and quantity not found for batch ID {} in batch_outputs table'.format(batchids[k][1]))
            batchids[k].append('')
            batchids[k].append('')

        # Getting equipment_id, timestamp, and comment from equipment_runs for each batch ID
        cur.execute("SELECT equipment_id, timestamp, comment, employee_id, recipe_id FROM equipment_runs WHERE batch_id='{}'".format(batchids[k][1]))
        results = sf.makeArray(cur.fetchall())

        recipeinfo = [batchids[k]]

        # Replacing equipment_id with nvn_eq_id
        if len(results) > 0:
            cur.execute("SELECT name, nvn_eq_id, process_id FROM equipment WHERE id={}".format(results[0][0]))
            equipment = sf.makeArray(cur.fetchall())
            nvn_eq_id = equipment[0][1]
            equipname = equipment[0][0]
            process_id = equipment[0][2]
            results[0][0] = nvn_eq_id

            # Using the recipe_id to get the recipe information
            if results[0][4] is not None:
                cur.execute("SELECT param_id, value_type, intvalue, floatvalue, stringvalue, datevalue FROM equipment_recipe_values WHERE recipe_id={}".format(results[0][4]))
                recipeinfo.append(sf.makeArray(cur.fetchall(),removeNone=True))

            
            # Getting parameter name and information from equipment_params using param_id
            if len(recipeinfo) > 1:
                for i in range(len(recipeinfo[1])):
                    try:
                        cur.execute("SELECT name, unit, param_type, tag_id FROM equipment_params WHERE id={}".format(recipeinfo[1][i][0]))
                        paraminfo = sf.makeArray(cur.fetchall())[0]
                        for element in paraminfo:
                            recipeinfo[1][i].append(element)
                    except:
                        # If the param_id is not in the equipment_params table, then fill in the info with ''
                        recipeinfo[1][i].append('')
                        recipeinfo[1][i].append('')
                        recipeinfo[1][i].append('')
                        recipeinfo[1][i].append('')


            # Getting the process from the process_id
            cur.execute("SELECT name FROM processes WHERE id={}".format(process_id))
            process = sf.makeArray(cur.fetchall())

            # Filling in info if present, or else filling in with ''
            batchids[k].insert(1,nvn_eq_id)     # Inserting nvn_eq_id into batchids
            batchids[k].append(results[0][1])   # Inserting date into batchids
            batchids[k].append(results[0][2])   # Inserting comment into batchids
            batchids[k].append(operators)   # Inserting employee_id into batchids
            batchids[k].append(equipname)       # Inserting equipment name into batchids
            batchids[k].insert(1,process[0][0]) # Inserting process into batchids


        else:
            print('Information not found for batch ID {} in equipment_runs table'.format(batchids[k][1]))
            print('Attempting to get information from UMCDB.batches...\n')


            # Attempting to get date, description, and operator ID from UMCDB.batches instad
            umccur.execute("SELECT a.manufactured_date, a.received_date, a.description, a.p_id, b.employee_id FROM \
                           batches a INNER JOIN employees b ON a.user_id = b.user_id WHERE batch_id='{}'".format(batchids[k][1]))
            results = sf.makeArray(umccur.fetchall())[0]

            if len(results) >= 5:

                # Getting the process from the process ID if process ID is not None
                if results[3] is not None:
                    cur.execute("SELECT name FROM processes WHERE id={}".format(results[3]))
                    process = sf.makeArray(cur.fetchall())
                    try:
                        results[3] = process[0][0]
                    except:
                        results[3] = ''

                else:
                    results[3] = ''

                # Adding the results to the batchids array
                batchids[k].insert(1,'')

                if results[1] is not None:
                    batchids[k].append(results[1])   # Inserting received_date into batchids
                else:
                    batchids[k].append(results[0])   # Otherwise inserting manufactured_date into batchids

                batchids[k].append(results[2])  # Inserting description into batchids

                batchids[k].append(operators)   # Inserting employee_ids into batchids

                batchids[k].append('')
                batchids[k].insert(1,results[3])    # Inserting process into batchids

            else:
                print('Information not found for batch ID {} in UMCDB.batches table\n'.format(batchids[k][1]))
                # If the date, description, and operator ID are not found, then fill in with ''
                batchids[k].insert(1,'')
                batchids[k].append('')
                batchids[k].append('')
                batchids[k].append('')
                batchids[k].append('')
                batchids[k].insert(1,'')


        # Calculating the total weight in and out for each batch ID from transfer bottles
        # Determining the units of the quantity
        try:
            units = batchids[k][5].split()[1]
        except:
            units = ''
        totalweightin, totalweightout = sf.transferBottles(batchids[k][3], pdf, writetopdf=False)

        # Inserting total weight out into batchids[k][5]
        batchids[k][5] = [batchids[k][5],str(totalweightout) + ' ' + units]



        # Adding in the recipe information gathered above
        batchrecipes.append(recipeinfo)

    return batchrecipes
# Returns batchrecipes


# Getting all equipment names from the database
def getEquipmentNames():

    cur.execute("SELECT nvn_eq_id FROM equipment WHERE name LIKE 'Sintering Furnace%'")
    sinteringfurnaces = [x[0] for x in sf.makeArray(cur.fetchall())]

    cur.execute("SELECT nvn_eq_id FROM equipment WHERE name LIKE 'Jet Mill%'")
    jetmills = [x[0] for x in sf.makeArray(cur.fetchall())]

    cur.execute("SELECT nvn_eq_id FROM equipment WHERE name LIKE 'Outgassing%'")
    ogs = [x[0] for x in sf.makeArray(cur.fetchall())]

    cur.execute("SELECT nvn_eq_id FROM equipment WHERE name LIKE 'HD Mixing%'")
    hds = [x[0] for x in sf.makeArray(cur.fetchall())]

    return sinteringfurnaces, jetmills, ogs, hds
# Returns sinteringfurnaces, jetmills, ogs, hds


# Adding in a header with batch information
def batchInfo(batchid, batchids):

    # Setting the process of the last batch ID to be Material Received, since it did not come from any other batches
    # Only doing this if there is more than one batch ID and the process is empty
    if len(batchids) > 1 and batchids[-1][1] == '':
        batchids[-1][1] = 'Material Received'

    # Need batch ID, product ID, Quantity, description, final equipment, and manufacturing date
    # For now, final equipment will just be the equipment used for the input batch ID since there is no forward tracing yet
    pdf.add_page()

    # Writing the title for the title page
    pdf.set_font('Helvetica', 'b', 16)  
    pdf.ln(5)
    pdf.cell(0,5.5,'Production Report',0,1,'C')
    pdf.ln(10)

    # Writing all the batch information
    pdf.set_font('Helvetica', 'b', 14)
    pdf.write(5,'Final Batch Information')
    pdf.ln(10)
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(55,5.5,'Batch ID')
    pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
    pdf.multi_cell(85,5.5,batchid)
    pdf.multi_cell(55,5.5,'Product ID')
    pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
    pdf.multi_cell(85,5.5,str(batchids[0][4]) + ' (' + sf.productType(batchids[0][4]) + ')')
    pdf.multi_cell(55,5.5,'Final Process')
    pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
    pdf.multi_cell(85,5.5,batchids[0][1])
    pdf.multi_cell(55,5.5,'Final Equipment')
    pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
    pdf.multi_cell(105,5.5,batchids[0][9] + ' (' + batchids[0][2] + ')')
    pdf.multi_cell(55,5.5,'Output Quantity (Dashboard)')
    pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
    pdf.multi_cell(85,5.5,batchids[0][5][0])
    pdf.multi_cell(55,5.5,'Output Quantity (Transfer Bottles)')
    pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
    pdf.multi_cell(85,5.5,batchids[0][5][1])
    pdf.multi_cell(55,5.5,'Description')
    pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
    pdf.multi_cell(135,5.5,batchids[0][7])
    pdf.multi_cell(55,5.5,'Date')
    pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
    pdf.multi_cell(105,5.5,str(batchids[0][6]))


# Adding in a BH Loop
def addBHLoop(batchids):
    # Calling the function to create the BH loop image for the latest batch
    bhloop = bh.bhLoop(batchids[0][3], filepath)

    # Adding the BH loop image to the pdf if it exists
    if bhloop == True:
        pdf.ln(10)
        pdf.image(filepath + 'BHLoop_' + str(batchids[0][3]) +'.png', x=pdf.l_margin, y=pdf.get_y()+1, w=180, h=110)

        # Setting the pdf xy position to the bottom of the image
        pdf.set_xy(pdf.l_margin, pdf.get_y() + 115)

    # If the BH loop image does not exist, then print message saying so
    else:
        # Writing the message on the pdf
        pdf.set_font('Helvetica', '', 10)
        pdf.ln(10)
        pdf.cell(180,5.5,'No BH Loop image found for batch ID ' + str(batchids[0][3]) + '.')
        pdf.set_xy(pdf.l_margin, pdf.get_y() + 100)

        # Also writing the message to the console
        print('No BH Loop image found for batch ID ' + str(batchids[0][3]) + '.\n')


# Getting material production and traceability information
def traceability(batchids, type):

    # Creating a title for the section
    pdf.set_font('Helvetica', 'b', 14)
    pdf.write(5,'Material and Production Traceability')

    # Setting font and positions for the table
    pdf.set_font('Helvetica', '', 6)
    ybefore = pdf.get_y()
    pdf.set_x(pdf.l_margin)
    # Setting colors and line thicknesses 
    pdf.set_fill_color(240,248,255)
    pdf.set_line_width(0.5)
    # Changing the draw color to steel blue
    pdf.set_draw_color(70,130,180)

    # Creating the visual traceability table
    for j in range(len(batchids)):
        k = len(batchids)-j-1
        pdf.set_xy(pdf.l_margin + j*24, ybefore + 10)
        pdf.multi_cell(24,3,'\n\n' + batchids[k][3] + '\n' + batchids[k][4] + '\n' + batchids[k][1] + '\n' + batchids[k][5][1] + '\n\n', 
                    border='L', fill=True, align='L')
        
    # Setting the line width and color back to default for the rest of the PDF
    pdf.set_line_width(0.2)
    pdf.set_draw_color(0,0,0)

    # Adding a table with batch info for each process if report type is comprehensive
    if type == 'comprehensive':

        # Printing just the headers of the table
        steptableheader = ['Step', 'Process', 'Equipment', 'Batch', 'Product', 'Quantity (DB)', 'Quantity (TB)', 'Date', 'Description', 'Employee ID']
        pdf.ln(5)
        pdf.set_font('Helvetica','',8)

        for j in range(len(steptableheader)):
            if j == 0:
                pdf.cell(9,5,steptableheader[j],border=1, fill=True)
            elif j == 3:
                pdf.cell(15,5,steptableheader[j],border=1, fill=True)
            elif j == 1 or j == 8:
                pdf.cell(33,5,steptableheader[j],border=1, fill=True)
            else:
                pdf.cell(18,5,steptableheader[j],border=1, fill=True)
            
        
        # Printing the rest of the table
        pdf.set_xy(pdf.l_margin,pdf.get_y()+5)
        for element in batchids[::-1]:
            print(element)
            
            # First determining how many lines high the row will be, based on number of operators
            operators = element[8].split(', ')
            rowheight = len(operators) * 5

            # Determining how many lines will be needed to fit the description
            description = element[7]
            descriptionlines = 1
            while len(description) > 21:
                descriptionlines += 1
                description = description[21:]
            descriptionheight = descriptionlines * 5

            if descriptionheight > rowheight:
                rowheight = descriptionheight

            for j in range(len(element[:9])):

                # Some columns have different widths than others, which is determined below
                if j == 0:
                    pdf.cell(9,rowheight,str(element[j]),border=1, fill=True)
                elif j == 1:
                    pdf.cell(33,rowheight,str(element[j]),border=1)
                elif j == 3:
                    pdf.cell(15,rowheight,str(element[j]),border=1)
                elif j == 5:
                    pdf.cell(18,rowheight,str(element[j][0]),border=1)
                    pdf.cell(18,rowheight,str(element[j][1]),border=1)
                elif j == 6:
                    try:
                        pdf.cell(18,rowheight,str(element[j].date()),border=1)
                    except:
                        pdf.cell(18,rowheight,str(element[j]),border=1)
                elif j == 7:
                    y = pdf.get_y()
                    x = pdf.get_x()
                    pdf.multi_cell(33,5,str(element[j]),border='LRT',align='L')        # Truncating the comment if it's too long
                    # Manually drawing the bottom border of the cell
                    pdf.line(x,y+rowheight,x+33,y+rowheight)
                    pdf.set_xy(x + 33, y)
                elif j == 8:
                    y = pdf.get_y()
                    x = pdf.get_x()
                    # Printing the all operators separated by commas
                    pdf.multi_cell(18,5,str(element[j]),border='LRT')
                    # Manually drawing the bottom and right border of the cell
                    pdf.line(x,y+rowheight,x+18,y+rowheight)
                    pdf.line(x+18,y,x+18,y+rowheight)
                    pdf.set_y(y + rowheight)
                else:
                    pdf.cell(18,rowheight,str(element[j]),border=1)


# Creating a lab inspections table
def labInspections(batchids):

    # Adding a new page for the lab inspections table to go on, and writing a title
    pdf.add_page()
    pdf.set_font('Helvetica', 'b', 14)
    pdf.write(5, 'Lab Inspections')

    # Finding all lab inspections that were done for each batch
    labinspections = []
    for element in batchids:

        # Getting the step, process, batch, and product from the batchids array
        step = element[0]
        process = element[1]
        batch = element[3]
        product = element[4]

        # Abbreviating the process name if necessary
        if process == 'Sintering and Annealing':
            process = 'S & A'

        # Getting all entries in UMCDB.batch_outputs_inspections that have the same batch number
        umccur.execute("SELECT inspection_id, user_id, DATE(due_date), DATE(performed_on), assignee_id, checked_by_employee_id, rejected_by_employee_id FROM batch_outputs_inspections WHERE batch_id = '{}'".format(batch))
        inspections = sf.makeArray(umccur.fetchall())


        # Replacing inspection_id, user_id, assignee_id, checked_by_employee_id, and rejected_by_employee_id with their names
        for item in inspections:

            # Inserting step, process, batch, and product into each inspection
            item.insert(0, step)
            item.insert(1, process)
            item.insert(2, batch)
            item.insert(3, product)

            # Getting the type of inspection from inspection_id
            umccur.execute("SELECT name FROM inspections WHERE id = '{}'".format(item[4]))
            inspectiontype = sf.makeArray(umccur.fetchall())[0][0]
            # Abbreiviating the inspection type if necessary
            if inspectiontype == 'Surface Grinding':
                inspectiontype = 'S. Grinding'
            elif inspectiontype == 'Optical Microscope':
                inspectiontype = 'Opt. Micro.'
            elif inspectiontype == 'Thickness Analysis':
                inspectiontype = 'Th. Analysis'
            elif inspectiontype == 'Particle Size Analysis':
                inspectiontype = 'PSA'
            item[4] = inspectiontype

            # Getting the name of the user who performed the inspection from user_id
            if item[5] != None:
                try:
                    umccur.execute("SELECT p.firstname, p.lastname FROM people p \
                                   INNER JOIN users u ON p.id = u.person_id WHERE u.id = '{}'".format(item[5]))
                    name = sf.makeArray(umccur.fetchall())[0]
                    item[5] = name[0][0] + '. ' + name[1]
                except:
                    item[5] = 'None'

            # Getting the name of the user who was assigned the inspection from assignee_id
            if item[8] != None:
                try:
                    umccur.execute("SELECT p.firstname, p.lastname FROM people p \
                                INNER JOIN users u ON p.id = u.person_id INNER JOIN employees e \
                                ON u.id = e.user_id WHERE e.id = '{}'".format(item[8]))
                    name = sf.makeArray(umccur.fetchall())[0]
                    item[8] = name[0][0] + '. ' + name[1]
                except:
                    item[8] = 'None'

            # Getting the name of the user who checked the inspection from checked_by_employee_id
            if item[9] != None:
                try:
                    umccur.execute("SELECT p.firstname, p.lastname FROM people p \
                                    INNER JOIN users u ON p.id = u.person_id JOIN employees e \
                                    ON u.id = e.user_id WHERE e.id = '{}'".format(item[9]))
                    name = sf.makeArray(umccur.fetchall())[0]
                    item[9] = name[0][0] + '. ' + name[1]
                except:
                    item[9] = 'None'

            # Adding the inspection to the list of inspections
            labinspections.append(item)

    # Creating a table with all lab inspections, if there were any done
    if len(labinspections) > 0:
        # Printing just the headers of the table
        header = ['Step', 'Process', 'Batch', 'Product', 'Type', 'Added By', 'Due Date', 
                    'Performed', 'Assigned To', 'Checked By', 'Rejected By']
        pdf.set_xy(pdf.l_margin, pdf.get_y() + 10)
        pdf.set_font('Helvetica', '', 8)
        for k in range(len(header)):
            if k == 0:
                pdf.cell(10, 5, header[k], border=1, fill=True)
            elif k == 1:
                pdf.cell(24, 5, header[k], border=1, fill=True)
            elif k == 2 or k == 3:
                pdf.cell(15, 5, header[k], border=1, fill=True)
            else:
                pdf.cell(18, 5, header[k], border=1, fill=True)

        # Printing the rest of the table
        pdf.set_font('Helvetica','',7)
        for element in labinspections[::-1]:
            pdf.set_xy(pdf.l_margin,pdf.get_y()+5)
            for k in range(len(element)):
                if k == 0:
                    pdf.cell(10,5,str(element[k]),border=1, fill=True)
                elif k == 1:
                    pdf.cell(24,5,str(element[k]),border=1)
                elif k == 2 or k == 3:
                    pdf.cell(15,5,str(element[k]),border=1)
                else:
                    pdf.cell(18,5,str(element[k]),border=1)

    # If there were no lab inspections done, then print that there were none
    else:
        pdf.set_xy(pdf.l_margin, pdf.get_y() + 10)
        pdf.set_font('Helvetica', '', 10)
        pdf.write(5, 'No lab inspections were performed on these batches.')


# Finding the overall compositions for each batch that was tested
def overallCompositions(batchids):
    # Creating a list of elements that can be tested for in the ICP, ONH, and CS
    elementlist = ['Al','B','Ce','Co','Cu','Dy','Er','Eu','Fe','Ga','Gd','Hf','Ho','La','Mo','Nb','Nd',
                    'Ni','Pr','Si','Sm','Tb','Ti','V','W','Y','Yb','Zr','Ar','O','N','H','C','S']
    
    # Creating an empty list that will contain ICP information for each batch
    allicp = []

    # Adding a new page to the pdf if necessary
    if pdf.get_y() > 220:
        pdf.add_page()
    else:
        pdf.set_xy(pdf.l_margin, pdf.get_y() + 15)

    pdf.set_font('Helvetica', 'b', 14)
    pdf.write(5, 'Overall Composition')

    # Getting ICP and elemental analysis for each batch
    for entry in batchids:
        step = entry[0]
        process = entry[1]
        batch = entry[3]
        product = entry[4]

        # Getting the ICP analysis for each batch
        # First getting the measurement id for every test done for the batch
        umccur.execute("SELECT id, test_no, sample_no, DATE(timestamp) FROM results_icp_measurements WHERE batch_id = '{}'".format(batch))
        icp = sf.makeArray(umccur.fetchall())


        # Using the measurement ID to get the element and concentration data for each test
        for item in icp:
            umccur.execute("SELECT element, concentration FROM results_icp_measurement_elements WHERE results_icp_measurement_id = '{}'".format(item[0]))
            icpConcentrations = sf.makeArray(umccur.fetchall())

            # Adding the element and concentration data to the list of ICP analysis
            item.append(icpConcentrations)


        # Now, get the elemental analysis data for each batch
        # Getting the measurement ID for each elemental analysis test done for the batch
        umccur.execute("SELECT id, test_no, sample_no, DATE(timestamp) FROM results_elementanalyzer_measurements WHERE batch_id = '{}'".format(batch))
        elementanalyzer = sf.makeArray(umccur.fetchall())


        # Using the measurement ID to get the element and concentration data for each test
        for item in elementanalyzer:
            umccur.execute("SELECT element, value, repetition FROM results_elementanalyzer_measurement_elements WHERE results_elementanalyzer_measurement_id = '{}'".format(item[0]))
            eaConcentrations = sf.makeArray(umccur.fetchall())

            # Currently, eaConcentrations is of the following format:
            # [[element, concentration, repetition], [element, concentration, repetition], ...]

            # Checking to see if the repetition is avg. If so, that value will be used for the concentration
            avgeaConcentrations = []
            for element in eaConcentrations:
                if element[2] == 'avg':
                    avgeaConcentrations.append(element)

            
            # If there is no avg repetition, then the values will be averaged
            if len(avgeaConcentrations) == 0 and len(eaConcentrations) > 0:
                # Getting the average of the concentrations
                total = 0
                for element in eaConcentrations:
                    total += element[1]

                try:
                    average = round(total / len(eaConcentrations), 5)
                except:
                    # Accounting for the case where results are all zero, so there is no division by zero
                    average = 0

                # Adding the average to the list of eaConcentrations
                avgeaConcentrations.append([element[0], average, 'avg'])
                    

            # Adding the element and concentration data to the list of elemental analysis
            item.append(avgeaConcentrations)


        # If the date of the elemental analysis is the same as the date of the ICP, then the results should be combined
        for element in icp:
            # Creating a temporary list to hold all EA results for the same date
            temp = []

            for item in elementanalyzer:
                # Checking to see if the dates are the same
                if item[3] == element[3] and item[2] == element[2]:

                    # Adding the elemental analysis results to the temporary list
                    temp.append(item[4])


                # Finding the average O, N, H, C, and S values for the entries in temp
                onhcs = ['O', 'N', 'H', 'C', 'S']
                subarray = []
                for i in range(len(onhcs)):
                    total = 0
                    for j in range(len(temp)):
                        for k in range(len(temp[j])):
                            if temp[j][k][0] == onhcs[i]:
                                total += temp[j][k][1]
                        try:
                            average = round(total / len(temp), 5)
                        except:
                            average = 0

                    try:
                        subarray.append([onhcs[i], average])
                    except:
                        subarray.append([onhcs[i], 0])

            # Adding the average to the ICP results
            try:
                for x in subarray:
                    element[4].append(x)
            except:
                pass


        # Add a value of 0 for any elements that occur in elementlist but not in ICP
        for element in elementlist:
            # If the element is not in the ICP results, then add [element, 0] to the ICP results
            for item in icp:
                if element not in [i[0] for i in item[4]]:
                    item[4].append([element, 0])

        # Normalizing the ICP results
        for item in icp:
            # Getting the total of all the concentrations
            total = 0
            for element in item[4]:
                # If the element is not O, N, H, C, or S, then add it to the total. This is so that only the ICP results get normalized, and not the elementanalyzer results
                if element[0] not in ['O', 'N', 'H', 'C', 'S']:
                    total += float(element[1])

            # Normalizing the concentrations
            for element in item[4]:
                if element[0] not in ['O', 'N', 'H', 'C', 'S']:
                    try:
                        element[1] = round(float(element[1]) / total * 100, 2)
                    except:
                        element[1] = 0

            # Calculating the total of the normalized concentrations
            normalizedtotal = 0
            for element in item[4]:
                if element[0] not in ['O', 'N', 'H', 'C', 'S']:
                    normalizedtotal += element[1]

            # Adding a total to the end of the list
            item[4].append(['Total', round(normalizedtotal,1)])

        # Adding the batch number and ICP results to allicp
        allicp.append([batch, icp])


    def addICPTable(pdf, allicp):
        # Adding the ICP and elemental analysis to the pdf
        pdf.set_xy(pdf.l_margin, pdf.get_y() + 10)
        pdf.set_font('Helvetica', '', 8)
        pdf.set_line_width(0.5)

        # Determining where the top of the table is going to be
        top = pdf.get_y()

        # Creating the table header
        pdf.cell(14, 5, 'Element', 1, fill=True)

        # Writing the batch number as the column header
        for item in allicp:
            if len(item[1]) > 1:
                pdf.cell(9*len(item[1]), 5, item[0], 1, 0, 'C', fill=True)
            elif len(item[1]) == 1:
                pdf.cell(18, 5, item[0], 1, 0, 'C', fill=True)

        # A second row will be added to the table that shows the process for each batch
        pdf.set_xy(pdf.l_margin, pdf.get_y() + 5)
        pdf.cell(14, 5, '', 1, fill=True)
        for item in allicp:
            # Determining the process for each batch. The process will be batchids[0][1] if the batch number matches batchids[0][3]
            process = ''
            for i in range(len(batchids)):
                if item[0] == batchids[i][3]:
                    process = batchids[i][1]
            if len(item[1]) > 1:
                pdf.cell(9*len(item[1]), 5, process, 1, 0, 'C', fill=True)
            elif len(item[1]) == 1:
                if process == 'Material Received':
                    process = 'Material Rec'
                pdf.cell(18, 5, process, 1, 0, 'C', fill=True)


        # Creating the table body
        pdf.set_line_width(0.2)
        # Adding a 'Total' to the elementlist
        elementlist.append('Total')

        # Writing the table body
        for element in elementlist:

            # Setting the fill color to light orange if the element is O, N, H, C, or S
            if element in ['O', 'N', 'H', 'C', 'S']:
                element = element + ' (ppm)'
                pdf.set_fill_color(255, 204, 153)

            # Setting the fill color to light green if the element is Total
            elif element in ['Total']:
                pdf.set_fill_color(204, 255, 204)
            
            # Otherwise, setting the fill color to light blue
            else:
                pdf.set_fill_color(240, 248, 255)
            pdf.set_xy(pdf.l_margin, pdf.get_y() + 5)
            pdf.cell(14, 5, element, 1, fill=True) # Writing the element as the row header
            # Drawing a dark line on top of the cell if the element is O or Total
            if element in ['O (ppm)', 'Total']:
                pdf.set_line_width(0.5)
                pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x()-14, pdf.get_y())
                pdf.set_line_width(0.2)

            # Drawing a dark line on the left and right side of the cell
            pdf.set_line_width(0.5)
            pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x(), pdf.get_y()+5)
            pdf.line(pdf.get_x()-14, pdf.get_y(), pdf.get_x()-14, pdf.get_y()+5)
            pdf.set_line_width(0.2)

            # Writing the concentration for each batch
            for item in allicp:
                # First, drawing a dark line on the left and right side of the concentrations for that batch
                if len(item[1]) > 1:
                    pdf.set_line_width(0.5)
                    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x(), pdf.get_y()+5)
                    pdf.line(pdf.get_x()+9*len(item[1]), pdf.get_y(), pdf.get_x()+9*len(item[1]), pdf.get_y()+5)
                    pdf.set_line_width(0.2)
                elif len(item[1]) == 1:
                    pdf.set_line_width(0.5)
                    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x(), pdf.get_y()+5)
                    pdf.line(pdf.get_x()+18, pdf.get_y(), pdf.get_x()+18, pdf.get_y()+5)
                    pdf.set_line_width(0.2)

                # Then, writing the concentration amounts
                for i in item[1]:
                    for j in i[4]:
                        if j[0] in ['O', 'N', 'H', 'C', 'S']:
                            j[0] = j[0] + ' (ppm)'
                        if j[0] == element:
                            if len(item[1]) > 1:
                                # If the element is O, N, H, C, or S, then the concentration will be in ppm
                                if element in ['O (ppm)', 'N (ppm)', 'H (ppm)', 'C (ppm)', 'S (ppm)']:
                                    pdf.cell(9, 5, str(round(j[1]*1000, 2)), 1, 0, 'C')
                                else:
                                    pdf.cell(9, 5, str(round(j[1], 2)), 1, 0, 'C')
                                # Drawing a dark line on the top of the cell if the element is O or Total
                                if element in ['O (ppm)', 'Total']:
                                    pdf.set_line_width(0.5)
                                    pdf.line(pdf.get_x()-9, pdf.get_y(), pdf.get_x(), pdf.get_y())
                                    pdf.set_line_width(0.2)
                            elif len(item[1]) == 1:
                                # If the element is O, N, H, C, or S, then the concentration will be in ppm
                                if element in ['O (ppm)', 'N (ppm)', 'H (ppm)', 'C (ppm)', 'S (ppm)']:
                                    pdf.cell(18, 5, str(round(j[1]*1000, 2)), 1, 0, 'C')
                                else:
                                    pdf.cell(18, 5, str(round(j[1], 2)), 1, 0, 'C')
                                # Drawing a dark line on the top of the cell if the element is O or Total
                                if element in ['O (ppm)', 'Total']:
                                    pdf.set_line_width(0.5)
                                    pdf.line(pdf.get_x()-18, pdf.get_y(), pdf.get_x(), pdf.get_y())
                                    pdf.set_line_width(0.2)


        # Setting the line width and fill color back to normal
        pdf.set_line_width(0.2)
        pdf.set_fill_color(240, 248, 255)

    # Determining whether any ICP data was found
    createICPTable = False
    for item in allicp:
        if len(item[1]) > 0:
            createICPTable = True

    # If ICP data was found, then create the table
    if createICPTable:
        addICPTable(pdf, allicp)
    else:
        # If no ICP data was found (and therefore no table was created), then write that there was no ICP data
        pdf.set_xy(pdf.l_margin, pdf.get_y() + 15)
        pdf.set_font('Helvetica', '', 10)
        pdf.write(5, 'No ICP or ONHCS data was found for any of the batches')


# Flux loss analysis section
def fluxLossAnalysis(batchids):

    # Adding a new page if the flux analysis section will start too low
    if pdf.get_y() > 220:
        pdf.add_page()
    else:
        pdf.set_xy(pdf.l_margin, pdf.get_y() + 25)

    # Writing the title for the section
    pdf.set_font('Helvetica', 'b', 14)
    pdf.write(5, 'Flux Analysis')
    pdf.set_font('Helvetica', '', 8)
    
    # Getting the flux analysis for only the latest and earliest batch in batchids
    # Getting the flux analysis for the earliest batch first
    batchid = batchids[-1][3]
    umccur.execute("SELECT product_id, batch_id, temperature, magnetic_polarization, angular_deviation FROM results_fluxmeter_measurements WHERE batch_id = '{}' ORDER BY temperature, created_at".format(batchid))
    fluxanalysis = sf.makeArray(umccur.fetchall())

    # Inserting a number for each entry in fluxanalysis
    for k in range(len(fluxanalysis)):
        fluxanalysis[k].insert(0, k+1)
            
    
    # Getting the flux analysis for the latest batch
    batchid = batchids[0][3]
    umccur.execute("SELECT product_id, batch_id, temperature, magnetic_polarization, angular_deviation FROM results_fluxmeter_measurements WHERE batch_id = '{}' ORDER BY temperature, created_at".format(batchid))
    fluxanalysis2 = sf.makeArray(umccur.fetchall())

    # Inserting a number for each entry in fluxanalysis2
    for k in range(len(fluxanalysis2)):
        fluxanalysis2[k].insert(0, k+1)


    # Printing the first flux analysis table if there is any data
    if len(fluxanalysis) > 0:
        header = ['', 'Product', 'Batch', 'Temperature', 'Magnetic Polarization (T)', 'Angular Deviation (deg)']
        pdf.set_xy(pdf.l_margin, pdf.get_y() + 10)

        # Printing the header first
        for k in range(len(header)):
            if k == 0:
                pdf.cell(10, 4, header[k], border=1, fill=True)
            else:
                pdf.cell(35, 4, header[k], border=1, fill=True)

        # Printing the rest of the table
        for element in fluxanalysis:
            pdf.set_xy(pdf.l_margin, pdf.get_y() + 4)
            for i in range(len(element)):
                if i == 0:
                    pdf.cell(10, 4, str(element[i]), border=1, fill=True)
                else:
                    pdf.cell(35, 4, str(element[i]), border=1)

    # If there is no data, then a message will be printed
    else:
        pdf.set_xy(pdf.l_margin, pdf.get_y() + 10)
        pdf.set_font('Helvetica', '', 10)
        pdf.write(5, 'No flux data available for batch {}'.format(batchids[-1][3]))
        pdf.set_font('Helvetica', '', 8)

    # Printing the second flux analysis table if there is any data
    if len(fluxanalysis2) > 0:
        header = ['', 'Product', 'Batch', 'Temperature', 'Magnetic Polarization (T)', 'Angular Deviation (deg)']
        pdf.set_xy(pdf.l_margin, pdf.get_y() + 10)

        # Printing the header first
        for k in range(len(header)):
            if k == 0:
                pdf.cell(10, 5, header[k], border=1, fill=True)
            else:
                pdf.cell(35, 5, header[k], border=1, fill=True)

        # Printing the rest of the table
        for element in fluxanalysis2:
            pdf.set_xy(pdf.l_margin, pdf.get_y() + 5)
            for i in range(len(element)):
                if i == 0:
                    pdf.cell(10, 5, str(element[i]), border=1, fill=True)
                else:
                    pdf.cell(35, 5, str(element[i]), border=1)

    # If there is no data, then a message will be printed
    else:
        pdf.set_xy(pdf.l_margin, pdf.get_y() + 10)
        pdf.set_font('Helvetica', '', 10)
        pdf.write(5, 'No flux data available for batch {}'.format(batchids[0][3]))
        pdf.set_font('Helvetica', '', 8)


    ###########################
    # Flux Loss Analysis Plot #
    ###########################

    # Calculating the average magnetic polarization and angular deviation for each temperature, if flux data exists
    if len(fluxanalysis) > 0 or len(fluxanalysis2) > 0:
        flux = [fluxanalysis, fluxanalysis2]
        avgfluxes = []
        for element in flux:
            temperatures = []
            average = []
            for k in range(len(element)):
                # Getting the temperature
                temperature = element[k][3]

                # If the temperature has not been seen before, then add it to the list of temperatures
                if temperature not in temperatures:
                    temperatures.append(temperature)

                    # Getting the magnetic polarization and angular deviation for each temperature in fluxanalysis
                    values = []
                    for value in element:
                        if value[3] == temperature:
                            values.append(value[4:])

                    # Calculating the average magnetic polarization and angular deviation
                    total = 0
                    for value in values:
                        total += value[0]
                    element[k][4] = round(total / len(values), 2)

                    total = 0
                    for value in values:
                        total += value[1]
                    element[k][5] = round(total / len(values), 2)

                    # Adding the average magnetic polarization and angular deviation to a list
                    average.append([temperature, element[k][4], element[k][5]])
            
            # Adding the list of average magnetic polarization and angular deviation to a list
            avgfluxes.append(average)


        # Determining the percentage of flux loss from the beginning temperature
        # Since there are sometimes measurements at one temperature but not at others,
        # the average flux at 25 degrees will be taken, and then each point will be % difference from that

        # Getting the average flux at the lowest temperature
        avgfluxlow = avgfluxes[0][0][1]

        # Calculating the % difference from the average flux at the lowest temperature
        for element in flux:
            for k in range(len(element)):
                element[k].append(round((element[k][4] - avgfluxlow) / avgfluxlow * 100, 2))


        # Creating a scatter plot of the flux loss data
        # Creating the figure
        fig, ax1 = plt.subplots(figsize=(10,6))
        ax1.grid(linestyle='--', linewidth=1)

        # Plotting the flux loss data
        # Creating a list of colors to use for each batch
        colors = ['b', 'g', 'r', 'k', 'm', 'y', 'c']
        for k in range(len(flux)):
            x = [i[3] for i in flux[k]]
            y = [i[6] for i in flux[k]]
            try:
                label = 'Batch {}'.format(flux[k][0][2])
            except:
                label = ''
            ax1.scatter(x, y, label=label, color=colors[k])

        # Formatting the plot
        ax1.set_xlabel('Temperature (C)')
        ax1.set_ylabel('% Flux Loss')
        ax1.set_title('Flux Loss Analysis')
        ax1.legend(loc='lower left')

        # Saving the figure
        plt.savefig(filepath + 'fluxLoss.png', bbox_inches='tight')
        ax1.clear()
        plt.close()

        # Adding the figure to the PDF
        pdf.image(filepath + 'fluxLoss.png', x=pdf.l_margin, y=pdf.get_y() + 10, w=160, h=100)

        # Setting x and y to the bottom of the plot
        pdf.set_xy(pdf.l_margin, pdf.get_y() + 100)


# Density section
def densities(batchids):

    # Adding a new page to the pdf if necessary
    if pdf.get_y() > 220:
        pdf.add_page()
    else:
        pdf.set_xy(pdf.l_margin, pdf.get_y() + 25)
    
    pdf.set_font('Helvetica', 'b', 14)
    pdf.write(5, 'Density')
    densitycounts = []

    # Finding the average density measurement for just the first and last batch
    for element in batchids:

        batchid = element[3]
        try:
            # First matching the batch ID to the id in UMCDB.batches
            umccur.execute("SELECT id FROM batches WHERE batch_id = '{}'".format(batchid))
            batches_id = umccur.fetchone()[0]

            # Then using that ID to find the density measurements in UMCDB.density_measurements
            umccur.execute("SELECT measurement FROM density_measurements WHERE batch_id = '{}'".format(batches_id))
            results = umccur.fetchall()

        except:
            results = []
            print('No density measurements for batch {} in UMCDB.density_measurements. \nWill try UMCDB.results_permeameter_measurements instead.'.format(batchid))

        
        # If the density measurement exists, add it to the densities list. Otherwise add 0
        densities = []
        
        if len(results) > 0:
            for k in results:
                densities.append(k[0])

            # Finding the average density
            avg_density = round(sum(densities) / len(densities),3)
            densitycounts.append(len(densities))
        else:

            # Try to get the density from the results_permeameter_measurements table
            umccur.execute("SELECT density_g_cm3 FROM results_permeameter_measurements WHERE batch_id = '{}'".format(batchid))
            results = umccur.fetchall()

            if len(results) > 0:
                for k in results:
                    densities.append(k[0])

                # Finding the average density
                avg_density = round(sum(densities) / len(densities),3)
                densitycounts.append(len(densities))

            else:
                avg_density = 'N/A'
                densitycounts.append(0)

        # Adding the average density to the batchids list
        element.append(avg_density)

    # Creating a table with a column for each batch number, and the density underneath
    # Adding in the batch numbers
    pdf.set_xy(pdf.l_margin, pdf.get_y() + 15)
    pdf.set_font('Helvetica', '', 8)
    pdf.set_draw_color(175, 175, 175)

    pdf.cell(45, 5, 'Batch ID', border=1, fill=True)
    for element in [batchids[0], batchids[-1]]:
        pdf.cell(20, 5, str(element[3]), border=1, fill=True)

    # Adding in the density values
    pdf.set_xy(pdf.l_margin, pdf.get_y() + 5)
    pdf.cell(45, 5, 'Avg Density (g/cm^3)', border=1, fill=True)
    for element in [batchids[0], batchids[-1]]:
        pdf.cell(20, 5, str(element[-1]), border=1)


    # Adding in the number of density measurements
    pdf.set_xy(pdf.l_margin, pdf.get_y() + 5)
    pdf.cell(45, 5, '# Measurements', border=1, fill=True)
    for element in [densitycounts[0], densitycounts[-1]]:
        pdf.cell(20, 5, str(element), border=1)


# Particle size analysis section
def particleSizeAnalysis(batchids):

    # Adding a new page to the pdf if necessary
    if pdf.get_y() > 220:
        pdf.add_page()
    else:
        pdf.set_xy(pdf.l_margin, pdf.get_y() + 15)

    pdf.set_font('Helvetica', 'b', 14)
    pdf.write(5, 'Particle Size Analysis')

    pdf.set_y(pdf.get_y() + 10)

    # If PSA measurements were taken from the HD, OG, or JM, get that data
    allpsavalues = []
    for element in batchids:
        batchid = element[3]

        cur.execute("SELECT id, sample_no, DATE(timestamp) FROM eq_psa_runs WHERE batch_id = '{}'".format(batchid))
        eqpsaruns = sf.makeArray(cur.fetchall())

        # If there are PSA measurements, then get data from eq_psa_run_svalues
        if len(eqpsaruns) > 0:
            for run in eqpsaruns:
                sampleno = run[1]
                date = run[2]
                cur.execute("SELECT eq_psa_measurement_id, dv_10, dv_50, dv_90, span, d_3_2, d_4_3 FROM eq_psa_run_svalues WHERE eq_psa_run_id = '{}'".format(run[0]))
                psasvalues = sf.makeArray(cur.fetchall())

                # If there are multiple svalues results, then get the average
                if len(psasvalues) >= 1:
                    dv10 = []
                    dv50 = []
                    dv90 = []
                    span = []
                    d32 = []
                    d43 = []

                    for svalue in psasvalues:
                        for i in range(len(svalue[1:])):
                            # Convert the numerical portion of the item to a float
                            try:
                                newvalue = float(svalue[i+1].split(' ')[0])
                            except:
                                newvalue = float(svalue[i+1])
                            svalue[i+1] = newvalue

                        dv10.append(svalue[1])
                        dv50.append(svalue[2])
                        dv90.append(svalue[3])
                        span.append(svalue[4])
                        d32.append(svalue[5])
                        d43.append(svalue[6])

                    # Finding the average of each value
                    avg_dv10 = round(sum(dv10) / len(dv10), 3)
                    avg_dv50 = round(sum(dv50) / len(dv50), 3)
                    avg_dv90 = round(sum(dv90) / len(dv90), 3)
                    avg_span = round(sum(span) / len(span), 3)
                    avg_d32 = round(sum(d32) / len(d32), 3)
                    avg_d43 = round(sum(d43) / len(d43), 3)
                    try:
                        avg_dv9010 = round(avg_dv90 / avg_dv10, 3)
                    except:
                        avg_dv9010 = 0 # If dv10 is 0, then set dv9010 to 0

                    psasvalues = [element[0], element[1], batchid, sampleno, avg_dv10, avg_dv50, avg_dv90, avg_span, avg_dv9010, avg_d32, avg_d43, date]

                    # Adding the psavalues to the batchids list
                    allpsavalues.append(psasvalues)

    # Creating a table that displays the psa data
    header = ['Step', 'Process', 'Batch ID', 'Sample #', 'DV(10)', 'DV(50)', 'DV(90)', 'Span*', 'DV(90)/DV(10)', 'SMD', 'VMD', 'Date']
    pdf.set_xy(pdf.l_margin, pdf.get_y() + 5)
    pdf.set_font('Helvetica', '', 8)


    # Determining where the top of the table is going to be
    top = pdf.get_y()
    linelocations = [pdf.get_x()]

    # Writing the header, but only if there is data to write
    if len(allpsavalues) > 0:
        for k in range(len(header)):
            if k == 0:
                pdf.cell(10, 5, header[k], border=1, fill=True)
            elif k == 1:
                pdf.cell(18, 5, header[k], border=1, fill=True)
            elif k >= 4 and k <=7:
                pdf.cell(13, 5, header[k], border=1, fill=True)
            elif k == 8:
                pdf.cell(24, 5, header[k], border=1, fill=True)
            else:
                pdf.cell(17, 5, header[k], border=1, fill=True)

            # Getting the x location of some cells so that thicker lines can be drawn in some areas
            if k == 3 or k == 6 or k == 8 or k == 10 or k == 11:
                linelocations.append(pdf.get_x())


    # Writing the data
    pdf.set_xy(pdf.l_margin, pdf.get_y() + 5)
    for element in allpsavalues:
        for k in range(len(element)):
            if k == 0:
                pdf.cell(10, 5, str(element[k]), border=1, fill=True)
            elif k == 1:
                if element[k] == 'Material Received':
                    pdf.cell(18, 5, 'Material Rec', border=1)
                else:
                    pdf.cell(18, 5, str(element[k]), border=1)
            elif k >= 4 and k <=7:
                pdf.cell(13, 5, str(element[k]), border=1)
            elif k == 8:
                pdf.cell(24, 5, str(element[k]), border=1)
            else:
                pdf.cell(17, 5, str(element[k]), border=1)

        pdf.set_xy(pdf.l_margin, pdf.get_y() + 5)

    # Drawing the lines for the table, but only if the table was created
    if len(allpsavalues) > 0:
        pdf.set_draw_color(0, 0, 0)
        pdf.set_line_width(0.5)

        for location in linelocations:
            pdf.line(location, top, location, pdf.get_y())

        # Drawing lines at the top and bottom of the header row
        pdf.line(linelocations[0], top, linelocations[-1], top)
        pdf.line(linelocations[0], top + 5, linelocations[-1], top + 5)

        # Setting the line width back to normal
        pdf.set_line_width(0.2)
    
    # If there are no psa measurements, then display a message
    if len(allpsavalues) == 0:
        pdf.set_font('Helvetica', '', 10)
        pdf.write(5, 'No PSA measurements were found.')
        pdf.set_xy(pdf.l_margin, pdf.get_y() + 5)

    # Writing the equation for span, if there are psa measurements
    else:
        pdf.set_xy(pdf.l_margin, pdf.get_y() + 5)
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 5, '*Span = [DV(90) - DV(10)] / DV(50)', border=0, fill=False)


# Mass losses section
def massLosses(batchids):

    # Adding a new page to the pdf if necessary
    if pdf.get_y() > 220:
        pdf.add_page()
    else:
        pdf.set_xy(pdf.l_margin, pdf.get_y() + 25)
    
    pdf.set_font('Helvetica', 'b', 14)
    pdf.write(5, 'Quantity In and Out')

    # Adding an empty list to each element of batchids that will contain mass input data from each source
    for k in range(len(batchids)):
        batchids[k].append([])

    # Finding the mass input for each batch in batchids from UMCDB.batch_inputs, transfer bottles, and HMI
    for k in range(len(batchids)):

        umccur.execute("SELECT quantity, unit FROM batch_inputs WHERE batch_id = '{}'".format(batchids[k][3]))
        results = umccur.fetchall()

        # Combining the quantity and unit into a string, then adding to the batchids list
        if len(results) > 0:
            totalweight = 0
            for r in results:
                totalweight += r[0]
            mass_input = str(round(totalweight,2)) + ' ' + r[1]
            batchids[k][-1].append(mass_input)
        else:
            batchids[k][-1].append('N/A')

        # Getting total weight in from the transfer bottles
        totalweightin, totalweightout = sf.transferBottles(batchids[k][3], pdf, writetopdf=False)
        batchids[k][-1].append(str(totalweightin) + ' kg')

        # Getting the mass from HMI using the batch ID
        cur.execute("SELECT weight FROM equipment_run_weights WHERE equipment_run_id IN (SELECT id FROM equipment_runs WHERE batch_id = '{}')".format(batchids[k][3]))
        results = cur.fetchall()

        # If there are results, then add them to the element of the batchids list that has the other mass outputs
        if len(results) > 0:
            # Adding up the total weight from all the results
            totalweight = 0
            for r in results:
                totalweight += r[0]
            batchids[k][5].append(str(round(totalweight, 2)) + ' kg')
        else:
            batchids[k][5].append('N/A')

    # Using the output weight from each batch to be the input mass for the next batch
    for k in range(len(batchids)):
        if k == len(batchids) - 1:
            batchids[k][-1].append('N/A')
        else:
            batchids[k][-1].append(batchids[k+1][5][2])



    # Creating a table that displays mass losses for each step
    header = ['Step', 'Process', 'Batch ID', 'Qty In (DB)', 'Qty Out (DB)', 'Qty In (TB)', 'Qty Out (TB)', 'Qty In (HMI)', 'Qty Out (HMI)']
    pdf.set_xy(pdf.l_margin, pdf.get_y() + 10)
    pdf.set_font('Helvetica', '', 8)

    # Adding the header
    for k in range(len(header)):
        if k == 0:
            width = 10
        elif k == 1:
            width = 35
        else:
            width = 20
        pdf.cell(width, 5, header[k], border=1, fill=True)

    # Adding the data to the table
    for element in batchids[::-1]:
        print(element)
        print('\n\n')

        # Adding the data to the table
        pdf.set_xy(pdf.l_margin, pdf.get_y() + 5)
        pdf.cell(10, 5, str(element[0]), border=1, fill=True)
        pdf.cell(35, 5, str(element[1]), border=1)
        pdf.cell(20, 5, str(element[3]), border=1)
        pdf.cell(20, 5, str(element[-1][0]), border=1)
        pdf.cell(20, 5, str(element[5][0]), border=1)
        pdf.cell(20, 5, str(element[-1][1]), border=1)
        pdf.cell(20, 5, str(element[5][1]), border=1)
        pdf.cell(20, 5, str(element[-1][2]), border=1)
        pdf.cell(20, 5, str(element[5][2]), border=1)


# Product Usages section
def productUsages(batchid):

    # First, tracing the batchid forward to see if it was used in any other batches
    # Continue to trace forward until the batchid is not found in any other batches
    # This information will all be put into a sankey diagram using plotly so will need to be organized in a way that is conducive to that

    # Creating a list that will contain all of the batchids that were used in other batches
    batchidsused = []

    # Checking the last batchid to see if it was used in any other batches
    umccur.execute("SELECT batch_id FROM batch_inputs WHERE component_batch_id = '{}'".format(batchid))
    results = umccur.fetchall()

    # Creating a set of nested lists that will contain the batchid and the batchid that it was used in
    for result in results:
        batchidsused.append([batchid, result[0]])

    print('Original batchidsused: {}'.format(batchidsused))

    # If the batchid was used in other batches, then continue to trace forward
    while True:
        print('Tracing back again...')
        newbatchids = []
        print(len(batchidsused))
        for element in batchidsused:
            recentbatch = element[-1]
            print('\n\n\nrecentbatch: {}'.format(recentbatch))
            umccur.execute("SELECT batch_id FROM batch_inputs WHERE component_batch_id = '{}'".format(recentbatch))
            results = umccur.fetchall()
            print("SELECT batch_id FROM batch_inputs WHERE component_batch_id = '{}'".format(recentbatch))
            print('results: {}'.format(results))

            # Replacing that element with a list of the batchid and the batchid that it was used in, as well as previous batchids
            for result in results:
                print('\nresult[0] {}'.format(result[0]))
                newarray = [x for x in element] + [result[0]]
                print('newarray: {}'.format(newarray))
                if newarray is not None:
                    element.append(newarray)
                    newbatchids.append(result[0])

                    
            print('New batchidsused: {}'.format(batchidsused))

        # If no new batchids were found, then break out of the loop
        if len(newbatchids) == 0:
            break


######################################
# Specific Report Creation Functions #
######################################

# Comprehensive report
def comprehensiveReport(batchid, type, multiply=False, pdf=pdf):

    # Getting information about the previous batches
    batchids = getPrevBatches(batchid)

    # Product usages section
    # productUsages('B230014')

    # Getting recipe information for each batch
    batchrecipes = getBatchRecipes(batchids)

    # Getting all of the equipment names from the database
    sinteringfurnaces, jetmills, ogs, hds = getEquipmentNames()

    # Adding the header with batch information
    batchInfo(batchid, batchids)

    # Adding in a BH Loop if one exists
    addBHLoop(batchids)

    # Adding in material production and traceability sections
    traceability(batchids, type)

    # Adding in a table of all lab inspections
    labInspections(batchids)

    # Adding in a table of overall compositions for each batch that was tested in ICP or ONH
    overallCompositions(batchids)

    # Adding in a flux loss analysis section
    fluxLossAnalysis(batchids)

    # Adding in a density section
    densities(batchids)

    # Adding in a particle size analysis section
    particleSizeAnalysis(batchids)

    # Adding in a mass losses section
    massLosses(batchids)


    # For each batch in the batchids list, generate the correct type of report based on equipment name
    i = 0 # Iteration number
    for element in batchrecipes[::-1]:
        batch = element[0][3]

        print('\n\n\nCreating ' + element[0][1] + ' report for ' + batch + '...')

        # Making sintering furnace reports for the steps completed in the sintering furnaces
        if element[0][2] in sinteringfurnaces:
            rsf.makeReport(batchid=batch, runarray=element, filepath=filepath, multiply=multiply, reporttype=type,pdf=pdf,iteration=str(i))

        # Making PSA report for the step completed in the jet mill
        elif element[0][2] in jetmills:
            rjm.makeReport(runarray=element, filepath=filepath, pdf=pdf, reporttype=type, multiply=multiply)
                
        # Making HD report
        elif element[0][2] in hds:
            rhd.makeReport(runarray=element, filepath=filepath, pdf=pdf, reporttype=type, multiply=multiply)

        # Making the OG report
        elif element[0][2] in ogs:
            rog.makeReport(runarray=element, filepath=filepath, pdf=pdf, reporttype=type, multiply=multiply)

        # Making the sieving report
        elif element[0][1] == 'Sieving':
            rSieving.makeReport(runarray=element, filepath=filepath, pdf=pdf, reporttype=type, multiply=multiply)

        # Making the Roller Mixing report
        elif element[0][1] == 'Roller Mixing':
            rRM.makeReport(runarray=element, filepath=filepath, pdf=pdf, reporttype=type, multiply=multiply)

        else:
            # Creating a new page and header for each report added to this bigger report
            pdf.add_page()
            pdf.set_font('Helvetica', 'b', 16)  
            pdf.ln(5)
            pdf.write(5, 'Process ' + str(element[0][0]) + ' - ' + str(element[0][1]))
            pdf.ln(8)


            pdf.set_font('Helvetica', '', 10)
            pdf.multi_cell(55,5.5,'Batch ID')
            pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
            pdf.multi_cell(85,5.5,element[0][3])
            pdf.multi_cell(55,5.5,'Product ID')
            pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
            pdf.multi_cell(85,5.5,str(element[0][4]) + ' (' + sf.productType(element[0][4]) + ')')
            pdf.multi_cell(55,5.5,'Quantity (Dashboard)')
            pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
            pdf.multi_cell(85,5.5,element[0][5][0])
            pdf.multi_cell(55,5.5,'Quantity (Transfer Bottles)')
            pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
            pdf.multi_cell(85,5.5,element[0][5][1])
            pdf.multi_cell(55,5.5,'Quantity (HMI)')
            pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
            pdf.multi_cell(85,5.5,element[0][5][2])
            pdf.multi_cell(55,5.5,'Operator ID')
            pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
            pdf.multi_cell(85,5.5,element[0][8])
            pdf.multi_cell(55,5.5,'Description')
            pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
            pdf.multi_cell(105,5.5,str(element[0][7]))
            pdf.multi_cell(55,5.5,'Equipment')
            pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
            pdf.multi_cell(105,5.5,'N/A')
            pdf.multi_cell(55,5.5,'Date')
            pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
            pdf.multi_cell(105,5.5,str(element[0][6]))
            pdf.multi_cell(55,5.5,'Total Run Time')
            pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
            pdf.multi_cell(85,5.5,'N/A')
            pdf.multi_cell(55,5.5,'Power Consumption')
            pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
            pdf.multi_cell(85,5.5,'N/A')

            # If the process is not Material Received, then try to add transfer bottle information
            if element[0][1] != 'Material Received':
                try:
                    sf.transferBottles(element[0][3], pdf)
                    # Establishing the starttime and endtime for the process
                    # The start time will be the time of the earliest transfer bottle
                except:
                    pass
            else:
                try:
                    sf.transferBottles(element[0][3], pdf, received=True)
                except:
                    pass
        
        # Incrementing the iteration number
        i = i + 1


# Customer view report
def customerReport(batchid, type, multiply=False):

    # Getting information about the previous batches
    batchids = getPrevBatches(batchid)

    # Getting recipe information for each batch
    batchrecipes = getBatchRecipes(batchids)

    # Creating a shorter version of the batchids list
    # shortbatchids = createShortBatchids(batchids)

    # Getting all of the equipment names from the database
    sinteringfurnaces, jetmills, ogs, hds = getEquipmentNames()

    # Adding the header with batch information
    batchInfo(batchid, batchids)

    # Adding in a BH Loop if one exists
    addBHLoop(batchids)
    pdf.ln(15) # Adding some space for better formatting

    # Adding in material production and traceability sections
    traceability(batchids, type='customer')

    # Adding in a table of all lab inspections
    labInspections(batchids)

    # Adding in a table of overall compositions for each batch that was tested in ICP or ONH
    overallCompositions(batchids)       # Need to add shorter version


    # For each batch in the batchids list, generate the correct type of report based on equipment name
    i = 0 # Iteration number
    for element in batchrecipes:

        # Adding a page after every third process
        if i % 3 == 0:
            pdf.add_page()
        
        # Determining the batch number
        batch = element[0][3]

        print('\n\n\nCreating ' + element[0][1] + ' report for ' + batch + '...')

        # Making sintering furnace reports for the steps completed in the sintering furnaces
        if element[0][2] in sinteringfurnaces:
            rsf.makeReport(batchid=batch, runarray=element, filepath=filepath, multiply=multiply, reporttype=type,pdf=pdf,iteration=str(i))

        # Making JM report for the step completed in the jet mill
        elif element[0][2] in jetmills:
            rjm.makeReport(runarray=element, filepath=filepath, pdf=pdf, reporttype=type, multiply=multiply)
                
        # Making HD report
        elif element[0][2] in hds:
            rhd.makeReport(runarray=element, filepath=filepath, pdf=pdf, reporttype=type, multiply=multiply)

        # Making the OG report
        elif element[0][2] in ogs:
            rog.makeReport(runarray=element, filepath=filepath, pdf=pdf, reporttype=type, multiply=multiply)

        # Skipping the report for Material Received (Eventually will have to make a section for it)
        elif element[0][1] == 'Material Received':
            pass
        
        elif element[0][2] == '':
            # Creating a header for each report added to this bigger report
            pdf.set_font('Helvetica', 'b', 16)  
            pdf.ln(5)
            pdf.write(5, 'Process ' + str(element[0][0]) + ' - ' + str(element[0][1]))
            pdf.ln(8)


            pdf.set_font('Helvetica', '', 10)
            pdf.multi_cell(55,5.5,'Batch ID')
            pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
            pdf.multi_cell(85,5.5,element[0][3])
            pdf.multi_cell(55,5.5,'Product ID')
            pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
            pdf.multi_cell(85,5.5,str(element[0][4]))
            pdf.multi_cell(55,5.5,'Quantity')
            pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
            pdf.multi_cell(85,5.5,element[0][5])
            pdf.multi_cell(55,5.5,'Operator ID')
            pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
            pdf.multi_cell(85,5.5,element[0][8])
            pdf.multi_cell(55,5.5,'Description')
            pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
            pdf.multi_cell(105,5.5,element[0][7])
            pdf.multi_cell(55,5.5,'Equipment')
            pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
            pdf.multi_cell(105,5.5,element[0][9] + ' (ID: ' + element[0][2] + ')')
            pdf.multi_cell(55,5.5,'Manufacturing Date')
            pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
            pdf.multi_cell(105,5.5,element[0][6])
            pdf.multi_cell(55,5.5,'Total Run Time')
            pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
            pdf.multi_cell(85,5.5,'TOTAL RUN TIME')
            pdf.multi_cell(55,5.5,'Power Consumption')
            pdf.set_xy(55 + pdf.l_margin,pdf.get_y()-5.5)
            pdf.multi_cell(85,5.5,'POWER CONSUMPTION')
            pdf.ln(10)

        i = i + 1


# Single report
def singleReport(batchid, type, multiply=False):

    # Establishing the batchids and batchrecipes lists
    batchids = [[batchid]] # Just one batchid since the report type is single
    batchrecipes = getBatchRecipes(batchids)

    # Getting all of the equipment names from the database
    sinteringfurnaces, jetmills, ogs, hds = getEquipmentNames()

    batch = batchrecipes[0][0][3]
    print('\nCreating ' + batchrecipes[0][0][1] + ' report for ' + batch + '...')

    # Make the correct type of report based on the equipment ID
    if batchids[0][2] in sinteringfurnaces:
        if type == 'single':
            rsf.makeReport(batchid=batch, runarray=batchids[0], filepath=filepath, multiply=multiply, reporttype='single', pdf=pdf,iteration='')
        elif type == 'full':
            rsf.makeReport(batchid=batch, runarray=batchids[0], filepath=filepath, multiply=multiply, reporttype='full', pdf=pdf,iteration='')

    elif batchids[0][2] in jetmills:
        rjm.makeReport(runarray=batchrecipes[0], filepath=filepath, pdf=pdf, reporttype='singular', multiply=multiply)

    elif batchids[0][2] in hds:
        rhd.makeReport(runarray=batchrecipes[0], filepath=filepath, pdf=pdf, reporttype='singular', multiply=multiply)

    elif batchids[0][2] in ogs:
        rog.makeReport(runarray=batchrecipes[0], filepath=filepath, pdf=pdf, reporttype='singular', multiply=multiply)
    
    else:
        print('No report for this equipment')


#################################
# Main Report Creation Function #
#################################

def createReport(batchid, type, multiply=False):
    
    # If the report type is single or full, then create a single report
    if type == 'single' or type == 'full':
        singleReport(batchid, type, multiply)

    # If the report type is comprehensive, then create a comprehensive report
    elif type == 'comprehensive':
        comprehensiveReport(batchid, type, multiply)

    # If the report type is customer, then create a customer report
    elif type == 'customer':
        customerReport(batchid, type, multiply)

    # Outputting the PDF
    # Naming the PDF file that was created
    pdf.output(filepath + '/Report' + type + batchid + '.pdf','F')


# Creating a report
createReport(batchid='B230028', type='full', multiply=False)