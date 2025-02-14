#!/usr/bin/env python3

#  Creates the AEM3D Lake Model Water Quality Related Files
#
#  Time Series
#     Nutrient Series
#     Chlorophyl Series
#
#  Control File

from lib import *
import glob
import os
from string import Template
import numpy as np
import pandas as pd


'''
List of WQ control Files present in wq_files from AEM3D_prep_file
    carbon.dat
    cyano.dat
    fdiat.dat
    light.dat
    nitrogen.dat
    organic_matter.dat
    oxygen.dat
    phosphorus.dat
    ssol1.dat
    ssol2.dat
    ts_bottom_51.dat
    ts_surface_51.dat

Sample of files to create in infiles (one of each for each river source)
    Pike_River_WQ_C.dat     Constant for all sources
    Pike_River_WQ_DO.dat    Based on Bay Temp
    Pike_River_WQ_N.dat
    Pike_River_WQ_P.dat
    Pike_River_WQ_Phyto.dat
    Pike_River_WQ_Si.dat     Constant for all sources
    Pike_River_WQ_TSS.dat
Specifications per Dr. Clelia Luisa Marti : June 2020

DO Dissolved Oxygen (mg O /L)
Set dissolved oxygen equal to the saturated value for the water temperature
DO = (14.652 - 4.1022e-1 * WTR_TEMP + 7.991e-3 * (WTR_TEMP2) –
7.77774e-5 * (WTR_TEMP3))
(Rich 1973 from Henderson-Sellers 1984, Engineering Limnology)


Q Discharge (m^3/s)

TP Total Phosphorous (mg P /L)
PO4 Filterable Reactive Phosphorous (mg P /L)
DOPL Dissolved Organic Phosphorous (Labile) (mg P /L)
POPL Particulate Organic Phosphorous (Labile) (mg P /L)

Equation to estimate TP
TP = 0.011001 * z2 + 0.073104 * z + 0.091528
where z = (Q - 159.78)/132.64

PO4 = 0.1050 * TP
DOPL = 0.23275 * TP
POPL = 0.30875 * TP


TN Total Nitrogen (mg N /L)
NH4 Ammonium (mg N /L)
NO3 Nitrate (mg N /L)
DONL Dissolved Organic Nitrogen (Labile) (mg N /L)
PONL Particulate Organic Nitrogen (Labile) (mg N /L)

Equation to estimate TN
TN = 0.00407 * z2  + 0.12853 * z + 0.75675
where z = (Q-166.3734)/138.1476
NH4 = 0.1 * TN
NO3 = 0.4 * TN
DONL = 0.2375 * TN
PONL = 0.2375 * TN

DOCL Dissolved Organic Carbon (Labile) (mg C /L)
POCL Particulate Organic Carbon (Labile) (mg C /L)
DOCL = 4.750 (Set to a constant value)
POCL  = 4.750 (Set to a constant value)

SiO2 Silica (mg Si /L)
SiO2 = 2.5 (Set to a constant value)

SSOL1 Suspended Solids Group 1 (mg /L)
Equation to estimate SSOL1
SSOL1 = 17.7558 * z2 + 59.5663 * z + 48.0127
where z = (Q - 170.0903)/ 142.1835

'''

def gencarbonfile(theBay):
    #
    #   Carbon data time series
    #
    generate_file_from_template('wq_c.template.txt',
                                'WQ_C.dat',
                                theBay,
                                {'source_id_list': '  '.join(theBay.sourcelist),
                                 'firstdate': theBay.FirstDate,
                                 'lastdate': theBay.LastDate
                                })    


def gensilicafile(theBay):
    #
    #   Silica data time series
    #     constant value for all sources
    #     set start and stop dates in template that has all sources
    #
    generate_file_from_template('wq_si.template.txt',
                                'WQ_Si.dat',
                                theBay,
                                {'source_id_list': '  '.join(theBay.sourcelist),
                                 'firstdate': theBay.FirstDate,
                                 'lastdate': theBay.LastDate
                                })        


def genwqfiles (theBay):

    # print('That is some Quality Water, right there.')

    # print('Copy Bay Flow')
    flowdf = theBay.flowdf.copy()       # get flow dataframe from bay object
    # print('Copy Bay Temp')
    tempdf = theBay.tempdf.copy()       # copy of bay water temp dataframe

    # Dissolved Oxygen based on Water Temp
    tempdf['DO'] = 14.652 \
                 - 4.1022e-1  * tempdf['wtr_temp'] \
                 + 7.991e-3   * np.power(tempdf['wtr_temp'], 2) \
                 - 7.77774e-5 * np.power(tempdf['wtr_temp'], 3)

    #   write out DO file
    #       all the sources are modeled with same DO,
    #       in one file repeat the calculated series for each source

    filename = 'WQ_DO.dat'
    logger.info('Writing Dissolved Oxygen File ' + filename)

    pathedfile = os.path.join(theBay.infile_dir, filename)
    with open(pathedfile, mode='w', newline='') as output_file:

        theBay.addfile(fname=filename)        # remember generated bay files
        # output the header text
        output_file.write(
            '!-----------------------------------------------------!\n')
        output_file.write(
            '! Written by AEM3D_prep_IAM                           !\n')
        output_file.write('! Bay ID: ' + theBay.bayid +
                        '                            !\n')
        output_file.write(
            '!-----------------------------------------------------!\n')
        output_file.write('6 data sets\n')
        output_file.write('0 seconds between data\n')
        output_file.write('0 '+ '  '.join(theBay.sourcelist) + ' \n')
        # TODO- The number of DO columns should be auto-synched with the length of the sourcelist
        output_file.write('TIME	  DO  DO  DO  DO  DO  DO  DO  DO\n')

        # output the ordinal date and flow value time dataframe columns
        # TODO-  Match the number of DO dataseries columns to the auto-synch of the length of sourcelist
        tempdf.to_csv(path_or_buf=output_file, columns=['ordinaldate', 'DO', 'DO', 'DO','DO','DO','DO', 'DO', 'DO'], float_format='%.3f',
                    sep=' ', index=False, header=False)
    #
    #   End of Dissolved Oxygen From Temp
    #

    ##
    #
    #   Generate Phyto related series, FDIAT and CYANO
    #
    ##

    #
    # Write Phyto Files - fixed series, use templates and set $year
    #
    for templateFile in [f for f in os.listdir(theBay.template_dir) if 'WQ_Phyto' in f]:
        generate_file_from_template(templateFile,
                                    os.path.splitext(templateFile)[0]+'.dat',
                                    theBay,
                                    {'year': theBay.FirstDate[0:4]})
    #
    # End of Phyto File Generation
    #

    #
    #   Generate Source Specific P, N, TSS files
    #

    for baysource in theBay.sourcelist :

        bs_name = theBay.sourcemap[baysource]['name']

        #
        # Bring in P reduction csv
        #         Adapted from RCA file prep bcseries.r

        # TODO: Check for p_reductions to be present, if not, provide sample where p_redux = 1.0
        
        print('NOT NOT NOT Reading P Reduction CSV')
        p_redux = 1.0

        '''
        #p_reductions = read.csv('p_reductions.csv', row.names='year', check.names = FALSE)
        p_reductions = pd.read_csv('p_reductions.csv', delimiter=',', index_col='year')
        #print('P Reduction CSV read')
        #print(p_reductions.columns)
        #print(p_reductions)

        # Get the one line from the p_reduction table for the current year
        theyears_p_reductions = p_reductions.loc[THEBAY.year]

        logger.info(' Selecting for reduxP = ', SCENARIO.reduxP)

        ## Convert percent reduction for current scenario to a "percent of" and store (reduxP is scenario string)
        if (SCENARIO.reduxP == 'no_redux') :
                p_redux = (100 - theyears_p_reductions[['0_redux']]) / 100
        else:
                p_redux = (100 - theyears_p_reductions[[SCENARIO.reduxP]]) / 100
        '''
        #p_redux = (100 - theyears_p_reductions[['40_redux']]) / 100       # Fix This hardcoded redux reference
        logger.info(f'Scaling Flow by P_Redux: {p_redux}')

        phosdf = pd.DataFrame()
        phosdf['ordinaldate'] = flowdf['ordinaldate']
        cqVersion = 'BREE2021Quad'

        #TODO: Implement BREE2021Seg
        #TODO: Move all this junk to THEBAY, choose cqVersion at THEBAY creation

        if cqVersion == 'Clelia':
            # Clelia TP Concentration - Discharge Relationship
            #   Same for ALL ILS inputs!!
            zTP = (flowdf['msflow'] - 159.78) / 132.64
            phosdf['TP'] =  ( 0.011001 * np.power(zTP,2) + 0.073104 * zTP + 0.091528 ) * p_redux
        elif cqVersion == 'BREE2021Quad':
            # Takis' new quadratic CQ equations by stream derived from historical data
            if (
            bs_name.startswith('MissisquoiRiver') or 
            bs_name.startswith('RockRiver') or
            bs_name.startswith('PikeRiver')
            ):
                logQ = np.log10(flowdf['msflow'])
                phosdf['TP'] = np.power(10, (1.6884 - 0.7758 * logQ + 0.3952 * logQ * logQ)) * p_redux / 1000
            elif bs_name.startswith('JewettStevens'):
                logQ = np.log10(flowdf['jsflow'])
                phosdf['TP'] = np.power(10, (2.2845 + 0.5185 * logQ + 0.1995 * logQ * logQ)) * p_redux / 1000
            elif bs_name.startswith('MillRiver'):
                logQ = np.log10(flowdf['mlflow'])
                phosdf['TP'] = np.power(10, (1.7935 + 0.4052 * logQ + 0.1221 * logQ * logQ)) * p_redux / 1000
            else:
                raise Exception(f'CQ Equation for baysource={bs_name} not found for cqVersion={cqVersion}')
            
            # Remove low Q days because the log will cause their concentrations to 'blow up'
            phosdf.loc[flowdf['msflow'] < 0.1, 'TP'] = 0.0
            # phosdf['TP'].loc[flowdf['msflow'].copy() < 0.1] = 0.0
        else:
            raise Exception(f'cqVersion {cqVersion} not defined')

        # Same for cqVersion = Clelia or BREE2021
        #   Updated 2021.05.27 per WQS Docs
        if bs_name.startswith('MissisquoiRiver'):
            phosdf['PO4'] = 0.01401 * np.power(phosdf['TP'],0.319)
            phosdf['DOPL'] = 0.03268 * np.power(phosdf['TP'],0.319)
            phosdf['POPL'] = phosdf['TP'] - phosdf['PO4'] - phosdf['DOPL']
        elif(
        bs_name.startswith('RockRiver') or
        bs_name.startswith('PikeRiver') or
        bs_name.startswith('JewettStevens') or
        bs_name.startswith('MillRiver')
        ):
            phosdf['PO4'] = 0.1050 * phosdf['TP']
            phosdf['DOPL'] = 0.23275 * phosdf['TP']
            phosdf['POPL'] = 0.30875 * phosdf['TP']
        else:
            raise Exception(f'baysource={bs_name} not found when calculating phosphorus species')

        # print('Check of PO4 dataframe')
        # print(phosdf['PO4'])

        # Nitrogen Series
        nitdf = pd.DataFrame()
        nitdf['ordinaldate'] = flowdf['ordinaldate']
        zTN = (flowdf['msflow'] - 166.3734)/138.1476
        nitdf['TN'] = 0.00407 * np.power(zTN,2)  + 0.12853 * zTN + 0.75675
        nitdf['NH4'] = 0.1 * nitdf['TN']            # Updated 2021.05.27 per WQS Docs
        nitdf['NO3'] = 0.3 * nitdf['TN']
        nitdf['DONL'] = 0.1 * nitdf['TN']
        nitdf['PONL'] = 0.475 * nitdf['TN']

        # Suspended Solids Series
        ssdf = pd.DataFrame()
        ssdf['ordinaldate'] = flowdf['ordinaldate']
        zSS = (flowdf['msflow'] - 170.0903)/142.1835
        ssdf['SSOL1'] = 17.7558 * np.power(zSS,2)  + 59.5663 * zSS + 48.0127

        #
        # Write Phosophorus File
        #
        filename = bs_name + '_WQ_P.dat'
        logger.info('Generating Bay Source File: '+filename)

        # open the file in output directory
        pathedfile = os.path.join(theBay.infile_dir, filename)
        with open(pathedfile, mode='w', newline='') as output_file:

            theBay.addfile(fname=filename)    # remember generated file names

            # output the header text
            output_file.write('!-----------------------------------------------------!\n')
            output_file.write('! Written by AEM3D_prep_IAM                           !\n')
            output_file.write('! Bay ID: '+ theBay.bayid + '                         !\n')
            output_file.write('! Bay Source: ' + bs_name + '                         !\n')
            output_file.write('!-----------------------------------------------------!\n')
            output_file.write('3 data sets\n')
            output_file.write('0 seconds between data\n')
            output_file.write('0    ' + baysource + '  ' + baysource + '  ' + baysource + '\n')
            output_file.write('TIME      PO4	DOPL	POPL\n')

            # output the ordinal date and P values time dataframe columns
            phosdf.to_csv(path_or_buf = output_file, columns= ['ordinaldate', 'PO4', 'DOPL', 'POPL'], float_format='%.3f',
            sep=' ', index=False, header=False)

        #
        # Write Nitrogen File
        #
        filename = bs_name + '_WQ_N.dat'
        logger.info('Generating Bay Source File: '+filename)

        # open the file in output directory
        pathedfile = os.path.join(theBay.infile_dir, filename)
        with open(pathedfile, mode='w', newline='') as output_file:

            theBay.addfile(fname=filename)    # remember generated file names

            # output the header text
            output_file.write('!-----------------------------------------------------!\n')
            output_file.write('! Written by AEM3D_prep_IAM                           !\n')
            output_file.write('! Bay ID: '+ theBay.bayid + '                         !\n')
            output_file.write('! Bay Source: ' + bs_name + '                         !\n')
            output_file.write('!-----------------------------------------------------!\n')
            output_file.write('4 data sets\n')
            output_file.write('0 seconds between data\n')
            output_file.write('0    ' + baysource + '  ' + baysource + '  ' + baysource + '  ' + baysource +'\n')
            output_file.write('TIME     NH4	NO3	DONL	PONL\n')

            # output the ordinal date and N values time dataframe columns
            nitdf.to_csv(path_or_buf = output_file, columns= ['ordinaldate', 'NH4', 'NO3', 'DONL', 'PONL'], float_format='%.3f',
            sep=' ', index=False, header=False)


        #
        # Write Total Suspended Solids File
        #
        filename = bs_name + '_WQ_TSS.dat'
        logger.info('Generating Bay Source File: '+filename)

        # open the file in output directory
        pathedfile = os.path.join(theBay.infile_dir, filename)
        with open(pathedfile, mode='w', newline='') as output_file:

            theBay.addfile(fname=filename)    # remember generated file names

            # output the header text
            output_file.write('!-----------------------------------------------------!\n')
            output_file.write('! Written by AEM3D_prep_IAM                           !\n')
            output_file.write('! Bay ID: '+ theBay.bayid + '                         !\n')
            output_file.write('! Bay Source: ' + bs_name + '                         !\n')
            output_file.write('!-----------------------------------------------------!\n')
            output_file.write('1 data sets\n')
            output_file.write('0 seconds between data\n')
            output_file.write('0    ' + baysource +'\n')
            output_file.write('TIME     SSOL1 \n')

            # output the ordinal date and TSS value time dataframe columns
            ssdf.to_csv(path_or_buf = output_file, columns= ['ordinaldate', 'SSOL1'], float_format='%.3f',
            sep=' ', index=False, header=False)

    gencarbonfile(theBay)   # one file for constant carbon data series
    gensilicafile(theBay)   # one file for constant silica data series
