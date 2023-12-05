# The purpose of this script is to create a BH Loop for a specified batch ID, and data from the M drive

"""
Notes:
    - Need to specify a better way to get the BH data file, in case there are multiple files with the same batch ID
    - Will switch to just plotting the BH loop from every file's data
"""

#################################
# Importing Necessary Libraries #
#################################

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os


###############################
# Data location and retrieval #
###############################

# Filepath where the BH data is located
bhfilepath = 'M:/equipment-data/permeameter/measured-data/BH/MP/_Online/csv_files/'

# Defining a function to retrieve the BH data given the batch ID, if it exists
def getBHdata(batchID):

    try:
        # Getting any file within the directory that contains the batch ID
        bhfiles = []
        for f in os.listdir(bhfilepath):
            if batchID in f:
                bhfiles.append(bhfilepath + f)
        # bhfile = bhfilepath + [f for f in os.listdir(bhfilepath) if batchID in f][0]
        # Checking to see if there are multiple files that contain the batch ID
        # print(len(bhfiles))

        # If there are multiple files, then get the most recent one
        if len(bhfiles) > 1:
            bhfiles.sort(key=os.path.getmtime)
            bhfile = bhfiles[-1]
        else:
            bhfile = bhfiles[0]

        # Reading the file into a dataframe
        bhdata = pd.read_csv(bhfile, header=0, index_col=False)

        # Creating a list with dataframes of each BH loop
        allbhdata = []
        for file in bhfiles:
            allbhdata.append(pd.read_csv(file, header=0, index_col=False))

        success = True

    except:
        bhdata = pd.DataFrame()
        allbhdata = [pd.DataFrame()]
        success = False

    # Returning the dataframe
    return allbhdata, bhdata, success


#############################################
# Creating the BH Loop and saving the image #
#############################################

def bhLoop(batchID, filepath):

    # Making batchID uppercase
    batchID = batchID.upper()

    # Getting the BH data
    allbhdata, bhdata, success = getBHdata(batchID)

    # If there was BH data, then create the plot using all of the data
    if success == True:

        # Creating the figure
        fig, ax1 = plt.subplots(figsize=(15,10))

        # Plotting the BH data
        for data in allbhdata:
            ax1.plot(data['H_kA_m'].to_numpy(), data['B_T'].to_numpy(), color='blue', label='BH Loop')
            ax1.plot(data['H_kA_m'].to_numpy(), data['J_T'].to_numpy(), color='blue', label='JH Loop')

        # Setting the x and y axis labels
        ax1.set_xlabel('[kA/m]', loc='left')
        ax1.set_ylabel('[T]', loc='top')
        
        # Setting the title based on how many results were found
        if len(allbhdata) == 1:
            ax1.set_title('BH Loop for Batch ' + batchID + '\n\n', fontsize=20)
        else:
            ax1.set_title('BH Loops for Batch ' + batchID + ' - ' + str(len(allbhdata)) + ' Results' + '\n\n', fontsize=20)

        # Setting the x and y axis limits
        ax1.set_xlim(-1600, 0)
        ax1.set_ylim(0, 1.4)

        # Setting the x and y axis grid lines
        ax1.grid(color='LightGray', linestyle='-', linewidth=1)

        # Setting the x and y axis borders
        ax1.spines['top'].set_visible(True)
        ax1.spines['right'].set_visible(True)

        # Adding a second y axis
        ax2 = ax1.twinx()
        ax2.set_ylabel('[kG]', loc='top')
        ax2.set_ylim(0, 14)

        # Adding a second x axis
        ax3 = ax1.twiny()
        ax3.set_xlabel('[kOe]', loc='left')
        ax3.set_xlim(-20, 0)

        # Adding a third x axis
        ax4 = ax1.twiny()
        ax4.set_xlabel('[T]', loc='left')
        ax4.set_xlim(-2, 0)

        # Shrinking the plot so that x and y axes will fit
        fig.subplots_adjust(bottom=0.25, right=0.85)

        # Setting all of the x axes to be at the bottom, and all y axes to be on the right
        ax1.xaxis.set_ticks_position('bottom')
        ax1.yaxis.set_ticks_position('right')
        ax2.yaxis.set_ticks_position('right')
        ax3.xaxis.set_ticks_position('bottom')
        ax4.xaxis.set_ticks_position('bottom')

        # Spacing the x axes
        ax1.spines['bottom'].set_position(('axes', 0))
        ax2.spines['bottom'].set_position(('axes', 0))
        ax3.spines['bottom'].set_position(('axes', -0.1))
        ax4.spines['bottom'].set_position(('axes', -0.2))

        # Placing x axis labels on the bottom
        ax1.xaxis.set_label_position('bottom')
        ax2.xaxis.set_label_position('bottom')
        ax3.xaxis.set_label_position('bottom')
        ax4.xaxis.set_label_position('bottom')

        # Spacing the y axes
        ax1.spines['right'].set_position(('axes', 1))
        ax2.spines['right'].set_position(('axes', 1.05))

        # Placing y axis labels on the right
        ax1.yaxis.set_label_position('right')
        ax2.yaxis.set_label_position('right')

        # Adding text under the x axes
        ax1.text(-800, -0.1, 'H', horizontalalignment='center', verticalalignment='center', fontsize=14)

        # Adding text to the right of the y axes
        ax1.text(40, 0.7, 'B, J', horizontalalignment='center', verticalalignment='center', rotation=90, fontsize=14)


        ############################
        # Radial Gridlines for P_c #
        ############################

        # Adding lines that will point radially outward from the origin, for the permeance coefficient
        # This will be done by plotting gray lines with the following slopes
        slopes = [-0.1, -0.2, -0.3, -0.5, -0.7, -1, -1.5, -2, -3, -5, -10]
        LD = [0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.7, 0.9, 1.3, 2.17]

        # Looping through the slopes
        for slope in slopes:
            # Creating the x and y values for the line
            x = np.linspace(-1600, 0, 10)
            y = slope * x * 0.001256637 # Converting y values to T from kA/m, and multiplying by slope
            # Adding the line to the figure
            ax1.plot(x, y, color='LightGray', linewidth=1)

            # If the line intersects the y axis below the y axis limit, add the text to the left of the line
            if y[0] < 1.4:
                ax1.text(-1600, y[0], 'Pc=' + str(-1*slope) + '\nL/D ~' + str(LD[slopes.index(slope)]), horizontalalignment='right', verticalalignment='center', fontsize=10)
            # If the line intersects the x axis above the y axis limit, add the text to the top of the plot where the line intersects the line y=1.4
            elif y[0] > 1.4:
                ax1.text(x[0] + (1.4 - y[0])/(slope*0.001256637), 1.4, 'Pc=' + str(-1*slope) + '\nL/D ~' + str(LD[slopes.index(slope)]), horizontalalignment='center', verticalalignment='bottom', fontsize=10)


        ##################
        # Finding BH Max #
        ##################

        # Doing this for all of the data
        for data in allbhdata:
            
            # Multiplying B and H together to find each product, then finding the maximum of all those
            BHmax = np.max([abs(a*b) for a,b in zip(bhdata['B_G'], bhdata['H_Oe']) if a>0])

            # Creating a dotted line representing -BHMax/H
            BHmaxH = [-BHmax/(1000*i) for i in np.linspace(-1, -20000, 1000)]
            ax2.plot(np.linspace(-1, -1600, 1000), BHmaxH, color='LightGray', linestyle='--', linewidth=1)

        # Fixing the layout of the figure so axes don't overlap
        # plt.show()
        plt.tight_layout()
        
        # Saving the figure
        fig.savefig(filepath + 'BHLoop_' + batchID + '.png', bbox_inches='tight')

    return success

# bhLoop('b230065', filepath='C:/Users/dluna/Desktop/pythonProjects/sfReports/graphs/')