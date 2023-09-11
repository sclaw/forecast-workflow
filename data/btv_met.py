import requests
import json
import pandas as pd
import datetime
from datetime import date

def splitsky ( instring ) :
  thestring = str(instring)
  tokens = thestring.split(':')   # looking for at least one cover code marker :
  if len(tokens) > 1 :
    token = tokens[-2].split()[-1]  # keep the cover code just before last : marker
  else:
    token = " "     # any records without a : cover code separator end up as a blank
  return token

def sky2prop (theskycode) :
  skypropmap = {'CLR': 0.000, 'FEW': 0.250, 'SCT': 0.5000, 'BKN': 0.875, 'OVC': 1.000, 'VV': 1.000, ' ': 1.000}
  theprop = skypropmap[str(theskycode)]
  return theprop

def leavenotrace (precip) :
  if str(precip) == 'T' :
    return '0.0'
  else :
    return precip

def create_final_df(df, colToKeep, index):
    df = pd.DataFrame(data={colToKeep: df[colToKeep]}, index=pd.to_datetime(index))

def retrieve_data(startDate, endDate, variable):
	requeststring = 'https://www.ncei.noaa.gov/access/services/data/v1/'+\
							'?dataset=local-climatological-data'+\
							'&stations=72617014742'+\
							'&startDate='+\
								str(startDate)+\
							'&endDate='+\
								str(endDate)+\
							'&dataTypes='+\
                                variable+\
							'&format=json' 
	print(requeststring)
	result = requests.get(requeststring)
    
	print(result.text)

	return pd.DataFrame(result.json())
    

def get_data () :

		endday = date.today()
		d = datetime.timedelta(days = 90)
		startday = endday - d

		# requeststring = 'https://www.ncei.noaa.gov/access/services/data/v1/'+\
		#                         '?dataset=local-climatological-data'+\
		#                         '&stations=72617014742'+\
		#                         '&startDate='+\
		#                          str(startday)+\
		#                         '&endDate='+\
		#                          str(endday)+\
		#                         '&dataTypes=HourlyPrecipitation,HourlySkyConditions'+\
		#                         '&format=json' 
		# print(requeststring)
		# result = requests.get(requeststring)

		# df = pd.DataFrame(result.json())
        
		cloud_df = retrieve_data(startday, endday, 'HourlySkyConditions')
		precip_df = retrieve_data(startday, endday, 'HourlyPrecipitation')
        
		print(cloud_df)
		print(precip_df)
        
		returnDict = {}

		cloud_df['skycode'] = cloud_df['HourlySkyConditions'].apply(splitsky)
		cloud_df['TCDC'] = cloud_df['skycode'].apply(sky2prop)
        
		precip_df['RAIN'] = precip_df['HourlyPrecipitation'].apply(leavenotrace)

		returnDict['TCDC'] = create_final_df(cloud_df, 'TCDC', 'DATE')
		returnDict['RAIN'] = create_final_df(precip_df, 'RAIN', 'DATE')

		return dict
