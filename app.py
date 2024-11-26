import streamlit as st
import pandas as pd
import pandas as pd
import glob
import os
import helper
import traceback
from io import StringIO
import fitz  # pymupdf for PDF processing
from PIL import Image  # For handling image files
import csv
import base64
import io
from anthropic import Anthropic

# Initialize the Anthropic client
client = Anthropic()
MODEL_NAME = "claude-3-5-sonnet-20240620"

removed_rows_list = []
dfs = pd.DataFrame()  # Initialize `dfs` as an empty DataFrame

# placeholder for processed data files
column_names = ['City', 'Price', 'Quantity', 'Supplier', 'Container', 'Condition', 'Color', 'Comment']
dfs = pd.DataFrame(columns=column_names)

# cities
cities = [
    "Atlanta", "Baltimore", "Boston", "Charleston", "Charlotte",
    "Chicago", "Cincinnati", "Cleveland", "Columbus", "Dallas",
    "Denver", "Detroit", "El Paso", "Houston", "Indianapolis", "Jacksonville",
    "Kansas City", "Kansas", "Long Beach", "Louisville", "Memphis", "Miami",
    "Minneapolis", "Mobile", "Nashville", "New Orleans", "New York",
    "Norfolk", "Oakland", "Omaha", "Phoenix", "Portland", "Salt Lake City",
    "Savannah", "Tacoma", "St. Louis", "Tampa",
]

# Set up the Streamlit app title and description
st.title("Freedom Conex App")
st.write("Upload your files (PDF, XLSX, TXT, JPG) to process container data")

# Create a file uploader allowing multiple file types
uploaded_files = st.file_uploader(
    "Choose files to upload (PDF, XLSX, TXT, JPG)", 
    type=['pdf', 'xlsx', 'txt', 'jpg'], 
    accept_multiple_files=True
)

if st.button("Run"):
    if uploaded_files:
        for file in uploaded_files:
            file_name = os.path.basename(file.name)
            file_extension = os.path.splitext(file_name)[1].lower()

            if file_extension == '.xlsx':
                df = pd.read_excel(file)
                # part file path to get file name without extension
                file_name = os.path.basename(file_name).split('.')[0]
                st.write(f"Processing: {file_name}")

                if file_name == 'Hysun':
                    try:
                        df['Supplier'] = 'Hysun'
                        # rename columns
                        df.rename(columns={'Depot': 'City', 'Size': 'Container', 'QTY': 'Quantity'}, inplace=True)
                        # remove city not in cities
                        df["CityUnmodified"] = df["City"]
                        df['City'] = df['City'].apply(helper.hysun_standardize_cities)
                        df['City'] = df['City'].apply(helper.determine_city)
                        removed_rows_list.append(('hysun_unknown_city', df[df['City'] == "Unknown"]))
                        df = df[df['City'] != "Unknown"]
                        # transform price and quantity to float
                        df['Price'] = df['Price'].astype(str).str.strip()
                        df = df[df['Price'] != ''] 
                        df['Price'] = df['Price'].str.replace(',', '', regex=False).astype(float)
                        df['Quantity'] = df['Quantity'].astype(float)
                        # Add comment
                        df['Comment'] = df['Condition']+" "+df["Container"] + " " + df['CityUnmodified']
                        # extract color
                        df['Color'] = df['Condition'].apply(helper.hy_check_color)
                        # remove from list
                        df["Condition"]=df["Condition"].apply(helper.remove_list)
                        removed_rows_list.append(('hysun_remove_list', df[df['Condition'] == 'Unknown']))
                        df = df[df['Condition'] != 'Unknown']
                        # extract condition
                        df['Condition'] = df['Condition'].apply(helper.hy_determine_condition)
                        # Parse container information
                        df['Container'] = df['Container'].apply(helper.hysun_determine_container)
                        df['Container'] = df['Container'].apply(helper.determine_size_and_code)
                        removed_rows_list.append(('hysun_unknown_container', df[df['Container'] == "Unknown"]))
                        df = df[df['Container'] != "Unknown"]
                        # select columns
                        df = df[['City', 'Price', 'Quantity', 'Supplier', 'Container', 'Condition', 'Color', 'Comment']]
                    except Exception as e:
                        print('Error in Hysun')
                        # Prints the type of the exception and the exception itself
                        print("Exception type:", type(e).__name__)
                        print("Exception message:", e)
                        # Prints the detailed traceback
                        traceback.print_exc()
        
                elif file_name == 'GCC':
                    try:
                        df['Supplier'] = 'GCC'
                        df['Type'] = df['Type'].apply(helper.gcc_determine_container)
                        # Remove unknown container types
                        unknown_type_df = df[df['Type'] == "Unknown"]
                        removed_rows_list.append(('gcc_unknown_type', unknown_type_df))
                        df = df[df['Type'] != "Unknown"]
                        # Remove type NaN
                        df = df[df['Type'].notna()]
                        # Remove none
                        df = df[df['Type'] != None]
                        # Combine columns into a list
                        df["20'"] = df.apply(lambda row: [row["20'"], row['Unnamed: 5']], axis=1)
                        del df['Unnamed: 5']
                        df["20'HC"] = df.apply(lambda row: [row["20'HC"], row['Unnamed: 7']], axis=1)
                        del df['Unnamed: 7']
                        df["40'"] = df.apply(lambda row: [row["40'"], row['Unnamed: 9']], axis=1)
                        del df['Unnamed: 9']
                        df["40HC"] = df.apply(lambda row: [row["40HC"], row['Unnamed: 11']], axis=1)
                        del df['Unnamed: 11']
                        # remove City not in cities
                        df['CityUnmodified'] = df['City']
                        df['City'] = df['City'].apply(helper.gcc_standardize_cities)
                        df['City'] = df['City'].apply(helper.determine_city)
                        removed_rows_list.append(('gcc_unknown_city', df[df['City'] == "Unknown"]))
                        df = df[df['City'] != "Unknown"]
                        # add comment
                        df['Comment'] = df['Condition'] + " " + df['Type']
                        # remove incoming containers (Condition has incoming)
                        removed_rows_list.append(('gcc_incoming', df[~df['Condition'].apply(helper.gcc_determine_incoming)]))
                        df = df[df['Condition'].apply(helper.gcc_determine_incoming)]
                        # extract color
                        df['Color'] = 'Unknown'
                        # Remove damaged containers
                        df["Condition"]=df["Condition"].apply(helper.damage_determine_condition)
                        # extract condition
                        df['Condition'] = df['Condition'].apply(helper.gcc_determine_condition)
                        # reshape data
                        df = pd.melt(df, id_vars=['City', 'Supplier', 'Condition', 'Type', 'Color', 'Comment'], value_vars=["20'", "20'HC", "40'", '40HC'],
                                    var_name='Size', value_name='Temp') ##### NEED TO SPLIT THIS UP AND FIGURE OUT WHAT IT IS DOING
                        # extract quantity and price, and remove rows with no quantity or price
                        df['Quantity'] = df['Temp'].apply(lambda x: x[0] if len(x) > 1 else None).astype(float)
                        df['Price'] = df['Temp'].apply(lambda x: x[1] if len(x) > 1 else None).astype(float)
                        df = df[df['Quantity'].notna() & df['Price'].notna()]
                        del df['Temp']
                        # derive container type
                        df['Container'] = df['Size'] + df['Type']
                        df['Container'] = df['Container'].apply(helper.determine_size_and_code)
                        removed_rows_list.append(('gcc_unknown_container', df[df['Container'] == "Unknown"]))
                        df = df[df['Container'] != "Unknown"]
                        del df['Size']
                        # Delete rows that aren't DC or Double Door type
                        del df['Type']
                        # select columns
                        df = df[['City', 'Price', 'Quantity', 'Supplier', 'Container', 'Condition', 'Color', 'Comment']]
                    except Exception as e:
                        print('Error in GCC')
                        # Prints the type of the exception and the exception itself
                        print("Exception type:", type(e).__name__)
                        print("Exception message:", e)
                        # Prints the detailed traceback
                        traceback.print_exc()
                
                elif file_name == 'CGK':
                    try:
                        df['Supplier'] = 'CGK'
                        # rename columns
                        df.rename(columns={'Location': 'City', 'Size': 'Container', 'QTY': 'Quantity'}, inplace=True)
                        # remove city not in cities
                        df["CityUnmodified"] = df["City"]
                        df['City'] = df['City'].apply(helper.cgk_standardize_cities)
                        df['City'] = df['City'].apply(helper.determine_city)
                        removed_rows_list.append(('cgk_unknown_city', df[df['City'] == "Unknown"]))
                        df = df[df['City'] != "Unknown"]
                        # transform price and quantity to float
                        df['Price'] = df['Price'].astype(float)
                        df['Quantity'] = df['Quantity'].astype(float)
                        # Add comment
                        df['Comment'] = df['Condition'] + " " +df['Container'] + " " + df['Color']
                        # extract color
                        df['Color'] = df['Color'].apply(helper.cgk_check_color)
                        # Determine if damage
                        df["Condition"]=df["Condition"].apply(helper.damage_determine_condition)
                        # extract condition
                        df['Condition'] = df['Condition'].apply(helper.cgk_determine_condition)
                        # Standardize container names
                        df['Container'] = df['Container'].apply(helper.determine_size_and_code)
                        removed_rows_list.append(('cgk_unknown_container', df[df['Container'] == "Unknown"]))
                        df = df[df['Container'] != "Unknown"]
                        # select columns
                        df = df[['City', 'Price', 'Quantity', 'Supplier', 'Container', 'Condition', 'Color', 'Comment']]
                    except Exception as e:
                        print('Error in CGK')
                        # Prints the type of the exception and the exception itself
                        print("Exception type:", type(e).__name__)
                        print("Exception message:", e)
                        # Prints the detailed traceback
                        traceback.print_exc()
                
                elif file_name == 'Kirin':
                    try:
                        df['Supplier'] = 'Kirin'
                        # rename columns
                        df.rename(columns={'Location': 'City', 'Size': 'Container', 'QTY': 'Quantity', 'Pick up': 'State'}, inplace=True)
                        # remove city not in cities
                        df["CityUnmodified"] = df["City"]
                        df['City'] = df['City'].apply(helper.kirin_standardize_cities)
                        df['City'] = df['City'].apply(helper.determine_city)
                        removed_rows_list.append(('kirin_unknown_city', df[df['City'] == "Unknown"]))
                        df = df[df['City'] != "Unknown"]
                        # remove unavailable containers
                        removed_rows_list.append(('kirin_unavailable', df[df["State"].apply(helper.kirin_check_available)!="Available"]))
                        df=df[df["State"].apply(helper.kirin_check_available)=="Available"]
                        # transform price and quantity to float
                        df['Price'] = df['Price'].str.replace('USD', '', regex=True).str.replace(',', '').astype(float)
                        df['Quantity'] = df['Quantity'].astype(float)
                        # extract color
                        df['Comment'] = df['Container'] + " " + df['Condition'] + " " + df['Depot']
                        df['Color'] = df['Condition'].apply(helper.kirin_check_color)
                        # Flag damaged containers
                        df["Condition"]=df["Condition"].apply(helper.damage_determine_condition)
                        # extract condition
                        df['Condition'] = df['Condition'].apply(helper.kirin_determine_condition)
                        # Standardize container names
                        df['Container'] = df['Container'].apply(helper.determine_size_and_code)
                        removed_rows_list.append(('kirin_unknown_container', df[df['Container'] == "Unknown"]))
                        df = df[df['Container'] != "Unknown"]
                        # select columns
                        df = df[['City', 'Price', 'Quantity', 'Supplier', 'Container', 'Condition', 'Color', 'Comment']]
                    except Exception as e:
                        print('Error in Kirin:')
                        # Prints the type of the exception and the exception itself
                        print("Exception type:", type(e).__name__)
                        print("Exception message:", e)
                        # Prints the detailed traceback
                        traceback.print_exc()

                elif file_name == 'NAC':
                    try:
                        df['Supplier'] = 'NAC'
                        # rename columns
                        df.rename(columns={'LOCATION': 'City', 'Size': 'Container', 'QTY': 'Quantity','PRICE':'Price'}, inplace=True)
                        # Remove state from city name
                        df['City'] = df['City'].ffill()
                        df['City'] = df['City'].apply(lambda x: x.split(",")[0])
                        # remove city not in cities
                        df["CityUnmodified"] = df["City"]
                        df['City'] = df['City'].apply(helper.nac_standardize_cities)
                        df['City'] = df['City'].apply(helper.determine_city)
                        removed_rows_list.append(('nac_unknown_city', df[df['City'] == "Unknown"]))
                        df = df[df['City'] != "Unknown"]
                        # transform price and quantity to float
                        df['Quantity'] = df['Quantity']#.astype(float)
                        # tag damage and for pickup asap / duocon
                        df["Condition"]=df["SIZE/CONDITION"].apply(helper.damage_determine_condition)
                        df['Condition']=df["Condition"].apply(helper.nac_determine_condition)
                        # extract condition and color
                        df['Color']=df['SIZE/CONDITION'].apply(helper.nac_check_color)
                        df['Comment'] = df['SIZE/CONDITION']
                        # Standardize container names
                        df['Container']=df['SIZE/CONDITION'].apply(helper.nac_determine_size_and_code)
                        removed_rows_list.append(('nac_unknown_container', df[df['Container'] == "Unknown"]))
                        df = df[df['Container'] != "Unknown"]
                        # Remove GATEBUY, OPEN SIDE, REEFER, TANK, OPEN, 4DOORS, 3DOORS, GENSET from df['SIZE/CONDITION']
                        df['SIZE/CONDITION']=df['SIZE/CONDITION'].apply(helper.nac_remove_list)
                        removed_rows_list.append(('nac_remove_list', df[df['SIZE/CONDITION'] == "Unknown"]))
                        df=df[df['SIZE/CONDITION']!="Unknown"]
                        # select columns
                        df = df[['City', 'Price', 'Quantity', 'Supplier', 'Container', 'Condition', 'Color', 'Comment']]
                    except Exception as e:
                        print('Error in NAC:')
                        # Prints the type of the exception and the exception itself
                        print("Exception type:", type(e).__name__)
                        print("Exception message:", e)
                        # Prints the detailed traceback
                        traceback.print_exc()

                elif file_name == 'New Way': 
                    try:
                        # Remove first row
                        df = df.iloc[1:]
                        df["20GP One-Trip\n (RAL1015, WFL+LB)"] = df.apply(lambda row: [row["20GP One-Trip\n (RAL1015, WFL+LB)"], row['Unnamed: 3']], axis=1)
                        del df['Unnamed: 3']
                        df["20GP CW"]=df.apply(lambda row: [row["20GP CW"], row['Unnamed: 5']], axis=1)
                        del df['Unnamed: 5']
                        df["40HC One-Trip\n (RAL1015, WFL+LB)"]=df.apply(lambda row: [row["40HC One-Trip\n (RAL1015, WFL+LB)"], row['Unnamed: 7']], axis=1)
                        del df['Unnamed: 7']
                        df["40HC CW"]=df.apply(lambda row: [row["40HC CW"], row['Unnamed: 9']], axis=1)
                        del df['Unnamed: 9']
                        df["40GP CW"]=df.apply(lambda row: [row["40GP CW"], row['Unnamed: 11']], axis=1)
                        del df['Unnamed: 11']
                        df["40HCDD 1-Trip (RAL\n 1015, WFL+LB)"]=df.apply(lambda row: [row["40HCDD 1-Trip (RAL\n 1015, WFL+LB)"], row['Unnamed: 13']], axis=1)
                        del df['Unnamed: 13']
                        df.rename(columns={'New Way': 'City'}, inplace=True)
                        df = pd.melt(df, id_vars=["City"], value_vars=["20GP One-Trip\n (RAL1015, WFL+LB)","20GP CW","40HC One-Trip\n (RAL1015, WFL+LB)","40HC CW","40GP CW","40HCDD 1-Trip (RAL\n 1015, WFL+LB)"],
                                            var_name='description', value_name='Temp')
                        df['Quantity'] = df['Temp'].apply(lambda x: x[0] if len(x) > 1 else None).astype(float)
                        df['Price'] = df['Temp'].apply(lambda x: x[1] if len(x) > 1 else None).astype(float)
                        # Remove rows with no quantity or price
                        removed_rows_list.append(('new_way_unknown_quantity_price', df[df['Quantity'].isna() | df['Price'].isna()]))
                        df = df[df['Quantity'].notna() & df['Price'].notna()]
                        # Split off the container information
                        df['Container'] = df['description'].apply(helper.determine_size_and_code)
                        removed_rows_list.append(('new_way_unknown_container', df[df['Container'] == "Unknown"]))
                        df = df[df['Container'] != "Unknown"]
                        df['Condition']=df['description'].apply(helper.new_way_determine_condition)
                        df['Color']=df['description'].apply(helper.new_way_determine_color)
                        df["Comment"] = df['description']+df["City"]
                        # Remove city not in cities
                        df['CityUnmodified'] = df['City']
                        df['City'] = df['City'].apply(helper.new_way_standardize_cities)    
                        df['City'] = df['City'].apply(helper.determine_city)
                        removed_rows_list.append(('new_way_unknown_city', df[df['City'] == "Unknown"]))
                        df = df[df['City'] != "Unknown"]
                        df['Supplier'] = 'New Way'
                        # Remove columns with NaN quantity or price
                        df = df.dropna(subset=['Quantity', 'Price'])
                        # select columns
                        df = df[['City', 'Price', 'Quantity', 'Supplier', 'Container', 'Condition', 'Color', 'Comment']]
                    except Exception as e:
                        print('Error in New Way:')
                        # Prints the type of the exception and the exception itself
                        print("Exception type:", type(e).__name__)
                        print("Exception message:", e)
                        # Prints the detailed traceback
                        traceback.print_exc()

                elif file_name == 'Seaco':
                    try:
                        df['Supplier'] = 'Seaco'
                        # rename columns
                        df.rename(columns={'Material description': 'Container', 'Grade': 'Condition'}, inplace=True)
                        # remove city not in cities
                        df["CityUnmodified"] = df["City"]
                        df['City'] = df['City'].apply(helper.seaco_standardize_cities)
                        df['City'] = df['City'].apply(helper.determine_city)
                        removed_rows_list.append(('seaco_unknown_city', df[df['City'] == "Unknown"]))
                        df = df[df['City'] != "Unknown"]
                        # transform price and quantity to float
                        df['Price'] = df['Price'].astype(float)
                        # Convert all values in 'Quantity' to strings, remove '+', and then convert to float
                        df['Quantity'] = df['Quantity'].apply(lambda x: str(x).replace('+', '')).astype(float)
                        # Add comment
                        df['Comment'] = df['Condition']+ " " + df["Container"].astype(str) + " " + df['CityUnmodified'] + " " + df['Depot Name']
                        # extract color - they do not have a color column
                        df['Color'] = 'Unknown'
                        # extract condition from grades
                        df['Condition'] = df['Condition'].apply(helper.seaco_determine_condition)
                        # Parse container information
                        df['Container'] = df['Container'].apply(helper.seaco_determine_size_and_code)
                        removed_rows_list.append(('seaco_unknown_container', df[df['Container'] == "Unknown"]))
                        df = df[~df['Container'].isin(["Unknown"])]
                        # select columns
                        df = df[['City', 'Price', 'Quantity', 'Supplier', 'Container', 'Condition', 'Color', 'Comment']]
                        # df.to_excel('Seaco_check.xlsx', index=False)
                    except Exception as e:
                        print('Error in Seaco')
                        # Prints the type of the exception and the exception itself
                        print("Exception type:", type(e).__name__)
                        print("Exception message:", e)
                        # Prints the detailed traceback
                        traceback.print_exc()

                elif file_name == 'Trident':
                    try:
                        df['Supplier'] = 'Trident'
                        # rename columns
                        df.rename(columns={'Location': 'City', 'Equipment type': 'Container'}, inplace=True)
                        # remove city not in cities
                        df["CityUnmodified"] = df["City"]
                        df['City'] = df['City'].apply(helper.trident_standardize_cities)
                        df['City'] = df['City'].apply(helper.determine_city)
                        removed_rows_list.append(('trident_unknown_city', df[df['City'] == "Unknown"]))
                        df = df[df['City'] != "Unknown"]
                        # transform price and quantity to float
                        df['Price'] = df['Price'].apply(lambda x: x.split(",-")[0])
                        # extract condition and color
                        df['CW/NEW'] = df['CW/NEW'].fillna("")
                        df['Container'] = df['Container'].fillna("")
                        df['RAL/YOM'] = df['RAL/YOM'].fillna("")
                        df['Comment'] = df['CW/NEW'] + " " + df['Container'] + " " + df['RAL/YOM']
                        df['Color'] = df["RAL/YOM"].apply(helper.trident_determine_color)
                        # Flag all with damaged condition
                        df['Condition'] = df['CW/NEW'].apply(helper.trident_determine_condition)
                        df['Container'] = df['Container'].apply(helper.determine_size_and_code)
                        df=df[df['Container']!="Unknown"]
                        removed_rows_list.append(('trident_unknown_container', df[df['Container'] == "Unknown"]))
                        # Remove list
                        removed_rows_list.append(('trident_remove_list', df[df['Comment'].apply(helper.remove_list)=="Unknown"]))
                        df['Comment']=df['Comment'].apply(helper.remove_list)
                        df=df[df['Comment']!="Unknown"]
                        #delete all rows with unknown container
                        removed_rows_list.append(('trident_unknown_container', df[df['Container'] == "Unknown"]))
                        df = df[df['Container'] != "Unknown"]
                        #delete all rows with open side container
                        removed_rows_list.append(('trident_open_side', df[df['Container'] == "Open Side"]))
                        df = df[df['Container'] != "Open Side"]
                        # select columns
                        df = df[['City', 'Price', 'Quantity', 'Supplier', 'Container', 'Condition', 'Color', 'Comment']]
                    except Exception as e:
                        print('Error in Trident:')
                        # Prints the type of the exception and the exception itself
                        print("Exception type:", type(e).__name__)
                        print("Exception message:", e)
                        # Prints the detailed traceback
                        traceback.print_exc()
                
                elif file_name == 'Ever Fortune':
                    try:
                        df["20 STD CW"] = df["20GP"]
                        df["40 STD CW"]=df["40GP"]
                        df["40 HC CW"]=df["40HC"]
                        df["20 STD NEW"]=df["20GP.1"]
                        df["20 HC NEW"]=df["20HC"]
                        df["40 HC NEW"]=df["40HC.1"]
                        df["20 STD DD NEW"]=df["20DD"]
                        df["20 HC DD NEW"]=df["40HCDD"]
                        # remove OPEN SIDE
                        df = df.drop(['20OS', '40HCOS'], axis=1)
                        # unpivot
                        df = pd.melt(df, id_vars=["City"], value_vars=['20 STD CW', '40 STD CW', '40 HC CW', '20 STD NEW', '20 HC NEW', '40 HC NEW', '20 STD DD NEW', '20 HC DD NEW'],
                                            var_name='Type', value_name='Temp')
                        # filter out empty records
                        df = df[df['Temp'].notnull()]
                        df['Temp'] = df['Temp'].astype(str)
                        # extract quantity
                        df['Quantity'] = df['Temp'].apply(helper.everfortune_convert_temp_to_qty)
                        # extract price
                        df['Price'] = df['Temp'].apply(helper.everfortune_convert_temp_to_price)
                        # standardize container
                        df['Container'] = df['Type'].str.rsplit(' ', n=1).str[0]
                        df['Condition'] = df['Type'].str.rsplit(' ', n=1).str[-1]
                        # extract color
                        df['Color'] = df['Temp'].apply(helper.everfortune_determine_color)
                        # add supplier
                        df['Supplier'] = 'Ever Fortune'
                        # add comment
                        df['Comment'] = df['Type'] + " " + df['Temp']
                        # standardize cities
                        df['City'] = df['City'].apply(helper.everfortune_standardize_cities)
                        # remove rows with 0 quantity or price
                        df = df[(df['Quantity'] != 0) & (df['Price'] != 0)]
                        # select columns
                        df = df[['City', 'Price', 'Quantity', 'Supplier', 'Container', 'Condition', 'Color', 'Comment']]
                    except Exception as e:
                        print('Error in Ever Fortune:')
                        # Prints the type of the exception and the exception itself
                        print("Exception type:", type(e).__name__)
                        print("Exception message:", e)
                        # Prints the detailed traceback
                        traceback.print_exc()
                
                elif file_name == 'Triton':
                    try:
                        df['Supplier'] = 'Triton'
                        # rename columns
                        df.rename(columns={'Depot': 'City', 'Size': 'Container', 'QTY': 'Quantity'}, inplace=True)
                        # remove city not in cities
                        df["CityUnmodified"] = df["City"]
                        df['City'] = df['City'].apply(helper.triton_standardize_cities)
                        df['City'] = df['City'].apply(helper.determine_city)
                        removed_rows_list.append(('triton_unknown_city', df[df['City'] == "Unknown"]))
                        df = df[df['City'] != "Unknown"]
                        df['Price'] = df['Price'].astype(float)
                        df['Quantity'] = df['Quantity'].astype(float)
                        # Add comment
                        df['Comment'] = df['Condition']+" "+ df["Container"].astype(str) + " " + df['CityUnmodified']
                        # extract color
                        df['Color'] = 'Unknown'
                        # Remove damaged containers
                        df["Condition"]=df["Condition"].apply(helper.damage_determine_condition)
                        # Parse container information
                        df['Container'] = df['Container'].apply(helper.triton_determine_size_and_code)
                        removed_rows_list.append(('triton_unknown_container', df[df['Container'] == "Unknown"]))
                        df = df[df['Container'] != "Unknown"]
                        # select columns
                        df = df[['City', 'Price', 'Quantity', 'Supplier', 'Container', 'Condition', 'Color', 'Comment']]
                    except Exception as e:
                        print('Error in Triton')
                        # Prints the type of the exception and the exception itself
                        print("Exception type:", type(e).__name__)
                        print("Exception message:", e)
                        # Prints the detailed traceback
                        traceback.print_exc()
                
                elif file_name == 'OVL':
                    try:
                        df['Supplier'] = 'OVL'
                        # rename columns
                        df.rename(columns={'Depot': 'City', 'Size': 'Container', 'QTY': 'Quantity'}, inplace=True)
                        # remove city not in cities
                        df["CityUnmodified"] = df["City"]
                        df['City'] = df['City'].apply(helper.ovl_standardize_cities)
                        df['City'] = df['City'].apply(helper.determine_city)
                        removed_rows_list.append(('ovl_unknown_city', df[df['City'] == "Unknown"]))
                        df = df[df['City'] != "Unknown"]
                        # transform price and quantity to float
                        df['Price'] = df['Price'].str.replace('USD', '').str.strip().astype(float)
                        # df['Price'] = df['Price'].astype(float)
                        df['Quantity'] = df['Quantity'].astype(float)
                        # Add comment
                        df['Comment'] = df['Condition']+" "+ df["Container"].astype(str) + " " + df['Color'] + " " + df['CityUnmodified']
                        # extract color
                        df['Color'] = df['Color'].astype(str).apply(helper.ovl_determine_color)
                        # Flag damaged containers
                        df["Condition"]=df["Condition"].apply(helper.damage_determine_condition)
                        # extract condition
                        df['Condition'] = df['Condition'].apply(helper.ovl_determine_condition)
                        # Parse container information
                        df['Container'] = df['Container'].apply(helper.ovl_determine_size_and_code)
                        removed_rows_list.append(('triton_unknown_container', df[df['Container'] == "Unknown"]))
                        removed_rows_list.append(('triton_remove_container', df[df['Container'] == "Remove"]))
                        df = df[~df['Container'].isin(["Unknown", "Remove"])]
                        # select columns
                        df = df[['City', 'Price', 'Quantity', 'Supplier', 'Container', 'Condition', 'Color', 'Comment']]
                    except Exception as e:
                        print('Error in OVL')
                        # Prints the type of the exception and the exception itself
                        print("Exception type:", type(e).__name__)
                        print("Exception message:", e)
                        # Prints the detailed traceback
                        traceback.print_exc()
                
                elif file_name == 'Florens':
                    try:
                        df['Supplier'] = 'Florens'
                        # rename columns
                        df.rename(columns={'Depot': 'City', 'Size': 'Container', 'QTY': 'Quantity', 'FLORENS': 'Price'}, inplace=True)
                        # remove city not in cities
                        df["CityUnmodified"] = df["City"]
                        df['City'] = df['City'].apply(helper.florens_standardize_cities)
                        df['City'] = df['City'].apply(helper.determine_city)
                        removed_rows_list.append(('florens_unknown_city', df[df['City'] == "Unknown"]))
                        df = df[df['City'] != "Unknown"]
                        # transform price and quantity to float
                        df['Price'] = df['Price'].astype(str).str.strip() 
                        df['Price'] = df['Price'].str.replace('$', '', regex=False).str.replace(',', '', regex=False).astype(float)
                        df['Quantity'] = df['Quantity'].astype(float)
                        # Add comment
                        df['Comment'] = df['Condition']+ " " + df["Container"].astype(str) + " " + df['CityUnmodified']
                        # extract color
                        df['Color'] = 'Unknown'
                        # Flag damaged containers- It just had WWT
                        df["Condition"]=df["Condition"].apply(helper.damage_determine_condition)
                        # Parse container information
                        df['Container'] = df['Container'].astype(str).apply(helper.florens_determine_size_and_code)
                        removed_rows_list.append(('florens_unknown_container', df[df['Container'] == "Unknown"]))
                        df = df[~df['Container'].isin(["Unknown"])]
                        # select columns
                        df = df[['City', 'Price', 'Quantity', 'Supplier', 'Container', 'Condition', 'Color', 'Comment']]
                        # df.to_excel('Florens_check.xlsx', index=False)
                    except Exception as e:
                        print('Error in Florens')
                        # Prints the type of the exception and the exception itself
                        print("Exception type:", type(e).__name__)
                        print("Exception message:", e)
                        # Prints the detailed traceback
                        traceback.print_exc()
                
                elif file_name == 'Shipped':
                    try:
                        df['Supplier'] = 'Shipped'
                        # rename columns
                        df.rename(columns={'Size': 'Container', 'Rating': 'Condition', 'Quantity Ready': 'Quantity', 'Wholesale Price': 'Price', 'Color Ral':'Color'}, inplace=True)
                        # remove city not in cities
                        df["CityUnmodified"] = df["City"]
                        df['City'] = df['City'].apply(helper.shipped_standardize_cities)
                        df['City'] = df['City'].apply(helper.determine_city)
                        removed_rows_list.append(('shipped_unknown_city', df[df['City'] == "Unknown"]))
                        df = df[df['City'] != "Unknown"]
                        # transform price and quantity to float
                        df['Price'] = df['Price'].astype(float)
                        df['Quantity'] = df['Quantity'].astype(float)
                        # Add comment
                        df['Comment'] = df['Condition']+ " " + df["Container"].astype(str) + " " + df["Color"] + " " + df['CityUnmodified'] + " " + df["Depot Name"] + " " + df["Bic Codes"]
                        # extract color
                        df['Color'] = df['Color'].astype(str).apply(helper.shipped_determine_color)
                        # Flag damaged containers
                        df["Condition"]=df["Condition"].apply(helper.damage_determine_condition)
                        # extract condition
                        df['Condition'] = df['Condition'].apply(helper.shipped_determine_condition)
                        # Parse container information
                        df['Container'] = df['Container'].astype(str).apply(helper.shipped_determine_size_and_code)
                        removed_rows_list.append(('shipped_unknown_container', df[df['Container'] == "Unknown"]))
                        df = df[~df['Container'].isin(["Unknown"])]
                        # select columns
                        df = df[['City', 'Price', 'Quantity', 'Supplier', 'Container', 'Condition', 'Color', 'Comment']]
                    except Exception as e:
                        print('Error in Shipped')
                        # Prints the type of the exception and the exception itself
                        print("Exception type:", type(e).__name__)
                        print("Exception message:", e)
                        # Prints the detailed traceback
                        traceback.print_exc()

                elif file_name == 'BAL':
                    try:
                        # For Quantity
                        df1 = df.iloc[:, :10]
                        # Rename the columns for clarity
                        df1.columns = ['Country', 'Port', 'Depot', '20GP(new)', '20GP(CW)', '40GP(new)', '40GP(CW)', '40HQ(new)', '40HQ(CW)', '40HQ(Double door )']
                        # Remove first row
                        df1 = df1.iloc[1:]
                        df1 = df1.melt(id_vars=["Country","Port", "Depot"], var_name="Container_Condition")
                        df1.rename(columns={'value': 'Quantity'}, inplace=True)
                        # For Price
                        # Calculate the indices for the columns to keep
                        num_columns = df.shape[1]  # Total number of columns
                        indices_to_keep = list(range(3)) + list(range(num_columns - 8, num_columns - 1))
                        # Select the columns using the calculated indices
                        df2 = df.iloc[:, indices_to_keep]
                        # Rename the columns for clarity
                        df2.columns = ['Country', 'Port', 'Depot', '20GP(new)', '20GP(CW)', '40GP(new)', '40GP(CW)', '40HQ(new)', '40HQ(CW)', '40HQ(Double door )']
                        # Remove first row
                        df2 = df2.iloc[1:]
                        df2 = df2.melt(id_vars=["Country","Port", "Depot"], var_name="Container_Condition")
                        df2.rename(columns={'value': 'Price'}, inplace=True)
                        df = pd.merge(df1, df2, on=["Country","Port", "Depot","Container_Condition"], how='left')
                        # Split 'Container_Condition' into two columns
                        df[['Container', 'Condition']] = df['Container_Condition'].str.extract(r'([^()]+)\(([^)]*)\)')
                        df = df.drop(columns=['Container_Condition'])
                        df['Supplier'] = 'BAL'
                        # rename columns
                        df.rename(columns={'Port': 'City'}, inplace=True)
                        # remove city not in cities
                        df["CityUnmodified"] = df["City"]
                        # Capitalize the values in the 'City' column
                        df['City'] = df['City'].str.capitalize()
                        df['City'] = df['City'].apply(helper.bal_standardize_cities)
                        df['City'] = df['City'].apply(helper.determine_city)
                        removed_rows_list.append(('BAL_unknown_city', df[df['City'] == "Unknown"]))
                        df = df[df['City'] != "Unknown"]
                        # transform price and quantity to float
                        df['Price'] = df['Price'].astype(float)
                        df['Quantity'] = df['Quantity'].astype(float)
                        # Add comment
                        df['Comment'] = df['Condition']+ " " + df["Container"].astype(str) + " " + df['CityUnmodified'] + " " + df["Depot"]
                        # extract color
                        df['Color'] = 'Unknown'
                        # Parse container information
                        df['Container'] = df['Container'].astype(str).apply(helper.bal_determine_size_and_code)
                        # Append " DD" to the Container column where Condition is "double door"
                        df.loc[df['Condition'] == 'Double door', 'Container'] = df['Container'] + ' DD'
                        # Flag damaged containers
                        df["Condition"]=df["Condition"].apply(helper.damage_determine_condition)
                        # extract condition
                        df['Condition'] = df['Condition'].apply(helper.bal_determine_condition)
                        removed_rows_list.append(('BAL_unknown_container', df[df['Container'] == "Unknown"]))
                        removed_rows_list.append(('BAL_unknown_container', df[df['Container'] == "Unknown DD"]))
                        df = df[~df['Container'].isin(["Unknown", "Unknown DD"])]
                        # select columns
                        df = df[['City', 'Price', 'Quantity', 'Supplier', 'Container', 'Condition', 'Color', 'Comment']]
                        # df.to_excel('BAL_check.xlsx', index=False)
                        df = df.groupby(['City', 'Price', 'Supplier', 'Container', 'Condition', 'Color'], as_index=False).agg({
                            'Quantity': 'sum',
                            'Comment': ' '.join  # Concatenate comments
                        })
                    except Exception as e:
                        print('Error in BAL')
                        # Prints the type of the exception and the exception itself
                        print("Exception type:", type(e).__name__)
                        print("Exception message:", e)
                        # Prints the detailed traceback
                        traceback.print_exc()


            # Process file based on its type
            elif file_extension == '.pdf':
                # part file path to get file name without extension
                file_name = os.path.basename(file_name).split('.')[0]
                st.write(f"Processing: {file_name}")

                if file_name == 'Conteira':
                    try:
                        final_table = []
                        with fitz.open(stream=file.read(), filetype="pdf") as doc:
                            for page_num in range(len(doc)):
                                print(f"Processing page {page_num + 1} of {len(doc)}")
                                page = doc.load_page(page_num)
                                text = page.get_text("text")
                        # Feed the page text to the Anthropic API
                        csv_output = helper.send_to_llm_api_conteira(text)
                        # Split the CSV string into rows and append to final_table
                        reader = csv.reader(csv_output.splitlines())
                        for row in reader:
                            final_table.append(row) 
                        df = pd.DataFrame(final_table[1:], columns=final_table[0])
                        #Data Pipeline
                        df['Supplier'] = 'Conteira'
                        # rename columns
                        df.rename(columns={'Quality': 'Condition', 'Type': 'Container', 'Qn': 'Quantity'}, inplace=True)
                        # remove city not in cities
                        df["CityUnmodified"] = df["City"]
                        df['City'] = df['City'].apply(helper.conteira_standardize_cities)
                        df['City'] = df['City'].apply(helper.determine_city)
                        removed_rows_list.append(('Conteira_unknown_city', df[df['City'] == "Unknown"]))
                        df = df[df['City'] != "Unknown"]
                        # transform price and quantity to float
                        df['Price'] = df['Price'].astype(str).str.strip() 
                        df['Price'] = df['Price'].str.replace('$', '', regex=False).astype(float)
                        df['Quantity'] = df['Quantity'].astype(float)
                        # Add comment
                        df['Comment'] = df['Condition']+ " " + df["Container"].astype(str) + " " + df['CityUnmodified'] + " " + df['Depot'] + " " + df['Note']
                        # extract color
                        # Apply the function to the 'Note' column
                        df['Color'] = df['Note'].apply(helper.conteira_extract_color)
                        # Flag damaged containers
                        df["Condition"]=df["Condition"].apply(helper.damage_determine_condition)
                        # extract condition
                        df['Condition'] = df['Condition'].apply(helper.conteira_determine_condition)
                        # Parse container information
                        df['Container'] = df['Container'].astype(str).apply(helper.conteira_determine_size_and_code)
                        removed_rows_list.append(('Conteira_unknown_container', df[df['Container'] == "Unknown"]))
                        df = df[~df['Container'].isin(["Unknown"])]
                        # select columns
                        df = df[['City', 'Price', 'Quantity', 'Supplier', 'Container', 'Condition', 'Color', 'Comment']]
                    except Exception as e:
                        print('Error in Conteira')
                        # Prints the type of the exception and the exception itself
                        print("Exception type:", type(e).__name__)
                        print("Exception message:", e)
                        # Prints the detailed traceback
                        traceback.print_exc()
                

            elif file_extension == '.jpg':
                final_table = []
                # Get the file name without extension
                file_name = os.path.basename(file.name).split('.')[0]
                st.write(f"Processing: {file_name}")
                binary_data = file.read()
                base_64_encoded_data = base64.standard_b64encode(binary_data)
                base64_string = base_64_encoded_data.decode('utf-8')
                # Send image to LLM API and get CSV output
                csv_output = helper.send_to_llm_api_sunbox(base64_string)
                # Split the CSV string into rows and append to final_table
                reader = csv.reader(csv_output.splitlines())
                for row in reader:
                    final_table.append(row)

                if file_name == 'SunBox':
                    try:
                        # Convert final_table to a pandas DataFrame
                        df = pd.DataFrame(final_table)
                        #st.write(df.head(10))
                        #st.write(df.columns)
                        # Data Pipeline
                        df = df.iloc[5:]
                        #st.write(df.head(10))
                        #st.write(df[1])
                        df["City"]=df[0]
                        df["20'_OT"] = df[1]
                        df["20 'DD_OT"]=df[2]
                        df["20 'OS_OT"]=df[3]
                        df["40 'GP_OT"]=df[4]
                        df["40 'HC_OT"]=df[5]
                        df["40 ' HCDD_OT"]=df[6]
                        df["20'_CW"]=df[7]
                        df["40'_CW"]=df[8]
                        df["40 'HC_CW"]=df[9]
                        #df.rename(columns={'SUN-BOX': 'City'}, inplace=True)
                        df = pd.melt(df, id_vars=["City"], value_vars=["20'_OT", "20 'DD_OT", "20 'OS_OT", "40 'GP_OT", "40 'HC_OT", "40 ' HCDD_OT", "20'_CW", "40'_CW", "40 'HC_CW"],
                                            var_name='description', value_name='Temp')
                        # Split off the quantity
                        df['Quantity'] = df['Temp'].apply(helper.sun_box_split_quantity)
                        #st.write(df.head(10))
                        # if quantity is not a number remove the row
                        removed_rows_list.append(('sun_box_unknown_quantity', df[~df['Quantity'].apply(lambda x: x.isnumeric())]))
                        df = df[df['Quantity'].apply(lambda x: x.isnumeric())]
                        # Split off the price
                        df['Price'] = df['Temp'].apply(helper.sun_box_split_price)
                        # Split off the condition
                        df['Condition'] = df['description'].apply(helper.sun_box_determine_condition)
                        # Remove city not in cities
                        df['CityUnmodified'] = df['City']
                        df['City'] = df['City'].apply(helper.sunbox_standardize_cities)
                        df['City'] = df['City'].apply(helper.determine_city)
                        removed_rows_list.append(('sun_box_unknown_city', df[df['City'] == "Unknown"]))
                        df = df[df['City'] != "Unknown"]
                        # Make comment
                        df["Comment"] = df['description']+df["City"]
                        # Generic columns
                        df['Supplier'] = 'Sun Box'
                        df['Color'] = "Unknown"
                        # Split off the container information
                        #df['Container'] = df['description'].apply(lambda x: x.split("_")[0])
                        df['Container'] = df['description'].apply(helper.determine_size_and_code)
                        removed_rows_list.append(('sun_box_unknown_container', df[df['Container'] == "Unknown"]))
                        df = df[df['Container'] != "Unknown"]
                        # select columns
                        df = df[['City', 'Price', 'Quantity', 'Supplier', 'Container', 'Condition', 'Color', 'Comment']]
                        #st.write(df.head(10))
                    except Exception as e:
                        print('Error in Sun Box')
                        # Prints the type of the exception and the exception itself
                        print("Exception type:", type(e).__name__)
                        print("Exception message:", e)
                        # Prints the detailed traceback
                        traceback.print_exc()

                     
            elif file_extension == '.txt':
                file_contents = file.read().decode("utf-8")
                # part file path to get file name without extension
                file_name = os.path.basename(file_name).split('.')[0]
                st.write(f"Processing: {file_name}")

                if file_name == 'OBLL':
                    try:
                        # Feed the text content to the Anthropic API
                        csv_output = helper.send_to_llm_api_obll(file_contents)
                        # Use StringIO to simulate a file object
                        csv_data = StringIO(csv_output)
                        # Read the CSV data into a Pandas DataFrame
                        df = pd.read_csv(csv_data)
                        #Data Pipeline
                        df['Supplier'] = 'OBLL'
                        # rename columns
                        df.rename(columns={'ColorCode': 'Color', 'ExtraComment': 'Note'}, inplace=True)
                        # remove city not in cities
                        df["CityUnmodified"] = df["City"]
                        df['City'] = df['City'].apply(helper.obll_standardize_cities)
                        df['City'] = df['City'].apply(helper.determine_city)
                        removed_rows_list.append(('OBLL_unknown_city', df[df['City'] == "Unknown"]))
                        df = df[df['City'] != "Unknown"]
                        # transform price and quantity to float
                        df['Price'] = df['Price'].astype(str).str.strip()
                        df = df[df['Price'] != ''] 
                        df['Price'] = df['Price'].str.replace('$', '', regex=False).astype(float)
                        df['Quantity'] = df['Quantity'].astype(float)
                        # Add comment
                        df['Comment'] = df["Container"].astype(str) + " " + df['Condition'] + " " + df['Color'] + " "  + df['CityUnmodified'] + " " + df['Location'] + " " + df['Note']
                        # extract color
                        df['Color'] = df['Color'].apply(helper.obll_determine_color)
                        # Extract condition and flag damaged containers
                        df["Condition"]=df["Condition"].apply(helper.obll_determine_condition)
                        # Parse container information
                        df['Container'] = df['Container'].astype(str).apply(helper.obll_determine_size_and_code)
                        removed_rows_list.append(('OBLL_unknown_container', df[df['Container'] == "Unknown"]))
                        df = df[~df['Container'].isin(["Unknown"])]
                        # select columns
                        df = df[['City', 'Price', 'Quantity', 'Supplier', 'Container', 'Condition', 'Color', 'Comment']]
                    except Exception as e:
                        print('Error in OBLL')
                        # Prints the type of the exception and the exception itself
                        print("Exception type:", type(e).__name__)
                        print("Exception message:", e)
                        # Prints the detailed traceback
                        traceback.print_exc()

                if file_name == 'Logwin':
                    try:
                        # Feed the text content to the Anthropic API
                        csv_output = helper.send_to_llm_api_logwin(file_contents)
                        csv_data = StringIO(csv_output)
                        # Read the CSV data into a Pandas DataFrame
                        df = pd.read_csv(csv_data)
                        #Data Pipeline
                        df['Supplier'] = 'Logwin'
                        # rename columns
                        df.rename(columns={'City and State': 'City', 'Type': 'Container', 'Comment': 'Note'}, inplace=True)
                        # remove city not in cities
                        df["CityUnmodified"] = df["City"]
                        df['City'] = df['City'].apply(helper.logwin_standardize_cities)
                        df['City'] = df['City'].apply(helper.determine_city)
                        removed_rows_list.append(('Logwin_unknown_city', df[df['City'] == "Unknown"]))
                        df = df[df['City'] != "Unknown"]
                        # transform price and quantity to float
                        df['Price'] = df['Price'].astype(str).str.strip()
                        df = df[df['Price'] != ''] 
                        df['Price'] = df['Price'].str.replace('$', '', regex=False).astype(float)
                        df['Quantity'] = df['Quantity'].astype(float)
                        # Add comment
                        df['Comment'] = df["Container"].astype(str) + " " + df['CityUnmodified'] + " " + df['Location'] + " " + df['Note']
                        # extract color
                        # Apply the function to the 'Note' column
                        df['Color'] = df['Container'].astype(str).apply(helper.logwin_determine_color)
                        # Extract condition and flag damaged containers
                        df["temp_condition"] = df["Container"] + " " + df["Note"].fillna("")
                        df["Condition"]=df["temp_condition"].astype(str).apply(helper.logwin_determine_condition)
                        # Parse container information
                        df['Container'] = df['Container'].astype(str).apply(helper.logwin_determine_size_and_code)
                        removed_rows_list.append(('Logwin_unknown_container', df[df['Container'] == "Unknown"]))
                        df = df[~df['Container'].isin(["Unknown"])]
                        # select columns
                        df = df[['City', 'Price', 'Quantity', 'Supplier', 'Container', 'Condition', 'Color', 'Comment']]
                    except Exception as e:
                        print('Error in Logwin')
                        # Prints the type of the exception and the exception itself
                        print("Exception type:", type(e).__name__)
                        print("Exception message:", e)
                        # Prints the detailed traceback
                        traceback.print_exc()
            else:
                print(file.name + ' not processed')
                continue
            dfs = pd.concat([dfs, df], ignore_index=True)

        dfs = dfs[~dfs['Price'].isin(['Please ask', 'Please offer'])] 
        dfs = dfs[dfs['Price'].notna()]
        dfs['Price'] = dfs['Price'].astype(float)
        dfs = dfs[dfs['Quantity'].notna()]
        dfs['Quantity'] = dfs['Quantity'].astype(int)
        dfs = dfs[dfs['Quantity'] != 0]
        # add key for ops inventory lookups
        dfs['Key'] = dfs['City'] + " " + dfs['Condition'] + " " + dfs['Container']
        # write to excel file
        dfs = dfs[list(('Key', 'City', 'Price', 'Quantity', 'Supplier', 'Container', 'Condition', 'Color', 'Comment'))]
        #dfs.to_excel('output.xlsx', index=False)
        # Generate Excel file in memory
        @st.cache_data
        def generate_excel_file(data_frame):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                data_frame.to_excel(writer, index=False, sheet_name="Sheet1")
                writer.save()
            return output.getvalue()
        # Streamlit download button for Excel
        st.download_button(
            label="Download the output as Excel",
            data=generate_excel_file(dfs),
            file_name="Inventory_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.info("Please upload one or more files to start processing.")