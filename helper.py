import re
import base64
import io
from anthropic import Anthropic

# Initialize the Anthropic client
client = Anthropic()
MODEL_NAME = "claude-3-5-sonnet-20240620"

def remove_list(condition):
    #GATEBUY, OPEN SIDE, REEFER, TANK, OPEN, 4DOORS, 3DOORS, GENSET 
    remove_list=["GATEBUY", "OPEN SIDE", "REEFER", "TANK", "OPEN", "4DOORS", "3DOORS", "GENSET","SIDE DOOR"]
    condition_upper=condition.upper()
    if isinstance(condition, str):
        #if condition contains any of the words in remove_list, return Remove
        if any(word in condition_upper for word in remove_list):
            return "Unknown"
        else:
            return condition
    else:
        return 'Unknown'

cities = [
    "Atlanta", "Baltimore", "Boston", "Charleston", "Charlotte",
    "Chicago", "Cincinnati", "Cleveland", "Columbus", "Dallas",
    "Denver", "Detroit", "El Paso", "Houston", "Jacksonville",
    "Kansas City", "Kansas", "Long Beach", "Louisville", "Memphis", "Miami",
    "Minneapolis", "Mobile", "Nashville", "New Orleans", "New York",
    "Norfolk", "Oakland", "Omaha", "Phoenix", "Portland", "Salt Lake City",
    "Savannah", "Tacoma", "St. Louis", "Tampa", "Indianapolis"
]

def determine_city(city):
    if isinstance(city, str):
        city_lower=city.lower()
        for city_name in cities:
            if city_name.lower() in city_lower:
                if city_name.lower()=="kansas":
                    return "Kansas City"
                return city_name
        return "Unknown"
    else:
        return "Unknown"


# Size and code helper functions
def determine_size_and_code(info):
    if isinstance(info, str):
        # get index of 20 or 40 with default value of -1
        index_20 = info.find('20')
        if index_20 != -1:
            code=get_code(info.upper(),index_20)
            if code!="Unknown":
                return("20 "+code)
        
        index_40 = info.lower().find('40')
        if index_40 != -1:
            code=get_code(info.upper(),index_40)
            if code!="Unknown":
                return("40 "+code)
        
        return "Unknown"

    else:
        return 'Unknown'
    
def get_code(info,index):
    numeric_over=False
    size_code_over=False


    code=""
    code_after_size=""

    for i in range(index,len(info)):
        # if character is uppercase letter
        if not info[i].isnumeric():
            numeric_over=True

        if numeric_over:
            if info[i].isupper():
                if size_code_over:
                    code_after_size+=info[i]

                if not size_code_over:
                    code+=info[i]
                    if len(code)>4:
                        size_code_over=True
            else:
                if len(code)>0:
                    size_code_over=True

    #code=="DC" or code=="GP":
    if "GD" in code or "GP" in code or "DC" in code:
        size_code="STD"
    elif "HC" in code or "HQ" in code:
        size_code="HC"
    else:
        size_code="STD"

    door_code=""
    if "DOUBLE DOOR" in info:
        door_code=" DD"
    if code[-2:]=="DD":
        door_code=" DD"
    if len(code_after_size)>1:
        if code_after_size[0:2]=="DD":
            door_code=" DD"

    return(size_code+door_code)
        


#################################################
#                  Damage                       #
#################################################
def damage_determine_condition(condition):
    if isinstance(condition, str):
        if 'asis' in condition.lower() or 'as-is' in condition.lower() or 'as_is' in condition.lower() or 'damage' in condition.lower():
            return 'DAMAGE'
        if "wwt" in condition.lower() or 'WWT' in condition:
            return 'WWT'
        else:
            return condition
    else:
        return 'Unknown'


#################################################
#                  HYSUN                        #
#################################################

def hy_check_color(condition):
    # Convert the string to lowercase to make the check case-insensitive
    condition_lower = condition.lower()
    
    # Check if both 'beige' and 'blue' are in the condition
    if 'beige' in condition_lower and 'blue' in condition_lower:
        return 'Mixed'
    # Check if only 'beige' is in the condition
    elif 'beige' in condition_lower:
        return 'Beige'
    # Check if only 'blue' is in the condition
    elif 'blue' in condition_lower:
        return 'Blue'
    elif "5010" in condition_lower:
        return 'Blue'
    elif "1015" in condition_lower:
        return 'Beige'
    else:
        return 'Unknown' 

def hy_determine_condition(condition):
    if ('iicl' in condition.lower()) or ('2 trip' in condition.lower()):
        return 'PRM'
    elif 'CW-WWT' in condition or 'CW-WWT ' in condition:
        return 'WWT'
    elif 'cw' in condition.lower():
        return 'CW'
    elif 'new' in condition.lower() or '1trip' in condition.lower():
        return 'NEW'
    elif 'damage' in condition.lower() or 'asis' in condition.lower() or 'as-is' in condition.lower() or 'as_is' in condition.lower():
        return 'DAMAGE'
    else:
        return 'Unknown'

def hysun_standardize_cities(value):
    if 'st' in value.lower() and 'louis' in value.lower():
        return 'St. Louis'
    elif 'saint' in value.lower() and 'louis' in value.lower():
        return 'St. Louis'
    elif 'fort worth' in value.lower():
        return 'Dallas'
    elif 'los angeles' in value.lower():
        return 'Long Beach'
    elif 'portland' in value.lower():
        return 'Portland'
    elif 'seattle' in value.lower():
        return 'Tacoma'
    else:
        return value

def hysun_determine_container(value):
    if 'os' in value.lower():
        return 'Unknown'
    elif ('4sd' in value.lower()) or ('3sd' in value.lower()) or ('2sd' in value.lower()) or ('3d' in value.lower()):
        return 'Unknown'
    else:
        return value

#################################################
#                    GCC                        #
#################################################
    
def gcc_determine_condition(condition):
    if '5iicl' in condition.lower() or "iicl" in condition.lower():
        return 'PRM'
    elif 'cw' in condition.lower():
        return 'CW'
    elif '1new' in condition.lower() or '1trip' in condition.lower():
        return 'NEW'
    elif 'damage' in condition.lower():
        return 'DAMAGE'
    else:
        return 'Unknown'

def gcc_determine_incoming(condition):
    if 'incoming' in condition.lower():
        return False
    else:
        return True

def gcc_determine_container(container):
    if isinstance(container, str):
        if "full open side" in container.lower():
            return "Unknown"
        elif ("dc" in container.lower()) or ("double door" in container.lower()):
            return container
    else:
        return 'Unknown'
    
def gcc_standardize_cities(value):
    if 'seattle' in value.lower():
        return 'Tacoma'
    else:
        return value


#################################################
#                    CGK                        #
#################################################

def cgk_check_color(condition):
    
    if isinstance(condition, str):
        # Convert the string to lowercase to make the check case-insensitive
        condition_lower = condition.lower()

        # Check if both 'beige' and 'blue' are in the condition
        if 'beige' in condition_lower and 'blue' in condition_lower:
            return 'Mixed'
        # Check if only 'beige' is in the condition
        elif 'beige' in condition_lower:
            return 'Beige'
        # Check if only 'blue' is in the condition
        elif 'blue' in condition_lower:
            return 'Blue'
        else:
            return 'Unknown' 
    else:
        return 'unknown'

def cgk_determine_condition(condition):
    if 'new' in condition.lower():
        return 'NEW'
    if '1 Trip' in condition:
        return 'NEW'
    elif 'cw' in condition.lower():
        return 'CW'
    elif 'damage' in condition.lower():
        return 'DAMAGE'
    else:
        return 'Unknown'

def cgk_standardize_cities(value):
    if 'newark' in value.lower():
        return 'New York'
    elif 'ST.LOUIS' in value:
        return 'St. Louis'
    elif 'seattle' in value.lower():
        return 'Tacoma'
    else:
        return value
    

#################################################
#                    KIRIN                      #
#################################################
    
def kirin_check_color(condition):
    # Convert the string to lowercase to make the check case-insensitive
    condition_lower = condition.lower()
    
    if "1015" in condition_lower and "5010" in condition_lower:
        return "Mixed"
    elif "1015" in condition_lower:
        return "Beige"
    elif "5010" in condition_lower:
        return "Blue"
    else:
        return "Unknown"

def kirin_determine_condition(condition):
    if 'cw' in condition.lower():
        return 'CW'
    elif 'damage' in condition.lower():
        return 'DAMAGE'
    else:
        return 'NEW'
    
def kirin_check_available(condition):
    if isinstance(condition, str):
        if 'unavailable' in condition.lower():
            return "Unavailable"
        else:
            return "Available"

def kirin_standardize_cities(value):
    if isinstance(value, str):
        if 'fort worth' in value.lower():
            return 'DALLAS, TX'
        elif 'cleveland' in value.lower():
            return 'CLEVELAND, OH'
        elif 'seattle' in value.lower():
            return 'Tacoma'
        else:
            return value
    else:
        return value

#################################################
#                    NAC                        #
#################################################


def nac_determine_size_and_code(info):
    if isinstance(info, str):
        # Use regex to find '20' or '40' at the start of the string or preceded by a space
        # Limit the search to the first 4 characters
        match_20 = re.search(r'^(.{0,3})(20)', info[:4])
        match_40 = re.search(r'^(.{0,3})(40)', info[:4])

        if match_20:
            index_20 = match_20.start()
            if match_20.group(1) == ' ':  # If preceded by a space, adjust index
                index_20 += 1
            code = get_code(info.upper(), index_20)
            if code != "Unknown":
                return "20 " + code
        
        elif match_40:
            index_40 = match_40.start()
            if match_40.group(1) == ' ':  # If preceded by a space, adjust index
                index_40 += 1
            code = get_code(info.upper(), index_40)
            if code != "Unknown":
                return "40 " + code
        
        return "Unknown"
    else:
        return 'Unknown'


def nac_check_color(condition):
    # Convert the string to lowercase to make the check case-insensitive
    if isinstance(condition, str):
        condition_lower = condition.lower()
        
        # Check if both 'beige' and 'blue' are in the condition
        if 'beige' in condition_lower and 'blue' in condition_lower:
            return 'Mixed'
        # Check if only 'beige' is in the condition
        elif 'beige' in condition_lower:
            return 'Beige'
        # Check if only 'blue' is in the condition
        elif 'blue' in condition_lower:
            return 'Blue'
        elif "1015" in condition_lower and "5010" in condition_lower:
            return 'Mixed'
        elif "1015" in condition_lower:
            return 'Beige'
        elif "5010" in condition_lower:
            return 'Blue'
        else:
            return 'Unknown'
    else:
        return 'Unknown'
    
def nac_determine_condition(condition):
    if isinstance(condition, str):
        if ('iicl' in condition.lower()) or ('two trip' in condition.lower()):
            return 'PRM'
        elif 'cw' in condition.lower():
            return 'CW'
        elif '1new' in condition.lower() or 'one tripper' in condition.lower() or "one trpper" in condition.lower() or 'onetripper' in condition.lower() or 'one triper' in condition.lower():
            return 'NEW'
        elif 'damage' in condition.lower():
            return 'DAMAGE'
        else:
            return condition
    else:
        return 'Unknown'
    
def nac_remove_list(condition):
    #GATEBUY, OPEN SIDE, REEFER, TANK, OPEN, 4DOORS, 3DOORS, GENSET 
    remove_list=["GAT", "GATEBUY", "OPEN SIDE", "REEFER", "TANK", "OPEN", "4DOORS", "3DOORS", "GENSET", "ARRIVING", "ASAP", "DUOCON", "WORKING REFEER", "40' HC WORKING REFEFER"]
    if isinstance(condition, str):
        #if condition contains any of the words in remove_list, return Remove
        if any(word in condition for word in remove_list):
            return "Unknown"
        else:
            return condition
    else:
        return 'Unknown'

def nac_standardize_cities(value):
    if 'charlotte' in value.lower():
        return 'Charlotte'
    elif 'chicago' in value.lower():
        return 'Chicago'
    elif 'dallas' in value.lower():
        return 'Dallas'
    elif 'el paso' in value.lower():
        return 'El Paso'
    elif ('long beach' in value.lower()) or ('los angeles' in value.lower()):
        return 'Long Beach'
    elif 'oakland' in value.lower():
        return 'Oakland'
    elif ('new york' in value.lower()) or ('newark' in value.lower()):
        return 'New York'
    elif 'SEATTLE' in value:
        return 'Tacoma'
    else:
        return value
    

#################################################
#                NEW WAY                        #
#################################################


def new_way_determine_condition(condition):
    if isinstance(condition, str):
        if 'cw' in condition.lower():
            return 'CW'
        elif '1-trip' in condition.lower() or 'one-trip' in condition.lower():
            return 'NEW'
        elif 'damage' in condition.lower():
            return 'DAMAGE'
        else:
            return 'Unknown'
    else:
        return 'Unknown'

def new_way_standardize_cities(value):
    if 'denver' in value.lower():
        return 'Denver'
    elif 'kansas city' in value.lower():
        return 'Kansas City'
    elif ('new york' in value.lower()) or ('newark' in value.lower()):
        return 'New York'
    elif 'memphis' in value.lower():
        return 'Memphis'
    elif 'minneapolis' in value.lower():
        return 'Minneapolis'
    elif 'st louis' in value.lower():
        return 'St. Louis'
    elif 'losangeles' in value.lower():
        return 'Long Beach'
    elif 'seattle' in value.lower():
        return 'Tacoma'
    else:
        return value
    
def new_way_determine_city(city):
    if isinstance(city, str):
        if city[-1].isdigit():
            return city[:-1]
        else:
            return city
    else:
        return 'Unknown'
    
def new_way_determine_color(color):
    if isinstance(color, str):
        if 'beige' in color.lower() and 'blue' in color.lower():
            return 'Mixed'
        elif 'beige' in color.lower():
            return 'Beige'
        elif 'blue' in color.lower():
            return 'Blue'
        elif '1015' in color.lower() and '5010' in color.lower():
            return 'Mixed'
        elif '1015' in color.lower():
            return 'Beige'
        elif '5010' in color.lower():
            return 'Blue'
        else:
            return 'Unknown'
    else:
        return 'Unknown'
    

#################################################
#                Sun Box                        #
#################################################

# Function to send image to the Anthropic API
def send_to_llm_api_sunbox(base64_string):
    message_list = [
        {
            "role": 'user',
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64_string}},
                {"type": "text", "text": "This image contains a table of shipping containers. Please extract the text in a comma separated value table structure. Do not modify or summarize any text. Make sure to capture all text and store it in the table structure. Keep the number of rows same as of the uploaded image. do not add or subtract the number of rows. keep the information same. Do not add or remove any information"}
            ]
        }
    ]
    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=4096,
        messages=message_list
    )
    return response.content[0].text

def sun_box_determine_condition(condition):
    if isinstance(condition, str):
        if 'cw' in condition.lower():
            return 'CW'
        elif 'ot' in condition.lower() or 'one-trip' in condition.lower():
            return 'NEW'
        elif "damage" in condition.lower() or "wwt" in condition.lower():
            return 'DAMAGE'
        else:
            return 'Unknown'
    else:
        return 'Unknown'

def sun_box_split_quantity(values):
    if isinstance(values, str):
        return values.split(" ")[0]
    else:
        return 'Unknown'
    
def sun_box_split_price(values):
    if '$' not in values:
        return None
    if isinstance(values, str):
        return values.split("$")[1].replace(",", "")
    else:
        return 'Unknown'
    
def sun_box_determine_city(city):
    if isinstance(city, str):
        if city[-1].isdigit():
            return city[:-1]
        else:
            return city
    else:
        return 'Unknown'
    
def sunbox_standardize_cities(value):
    if 'seattle' in value.lower():
        return 'Tacoma'
    else:
        return value
    
#################################################
#                Trident                        #
#################################################

def trident_standardize_cities(value):
    if isinstance(value, str):
        if 'Saint-Louis' in value:
            return 'St. Louis'
        elif 'seattle' in value.lower():
            return 'Tacoma'
        else:
            return value
    else:
        return 'Unknown'
    
def trident_determine_condition(condition):
    if isinstance(condition, str):
        
        if 'asis' in condition.lower() or 'damage' in condition.lower() or "wwt" in condition.lower():
            return 'DAMAGE'
        elif 'iicl' in condition.lower() or 'two trip' in condition.lower():
            return 'PRM'
        elif 'cw' in condition.lower():
            return 'CW'
        elif 'new' in condition.lower():
            return 'NEW'
        else:
            return 'Unknown'
    else:
        return 'Unknown'
    
def trident_determine_container(container):
    if isinstance(container, str):
        if "full open side" in container.lower():
            return "Open Side"
        else:
            return container
    else:
        return 'Unknown'
    
def trident_determine_color(ralyom):
    # - only RAL1015 -> BEIGE
    # - only RAL5010 -> BLUE
    # - RAL1015 + RAL5010 -> BEIGE AND BLUE
    # - anything else -> UNKNOWN
    if isinstance(ralyom, str):
        ralyom_lower = ralyom.lower()
        if '1015' in ralyom_lower and '5010' in ralyom_lower:
            return 'Mixed'
        elif '1015' in ralyom_lower:
            return 'Beige'
        elif '5010' in ralyom_lower:
            return 'Blue'
        else:
            return 'Unknown'


#################################################
#                Ever Fortune                   #
#################################################

def everfortune_convert_temp_to_qty(value):
    quantity = value.split('_')[0]
    return int(quantity)

def everfortune_convert_temp_to_price(value):
    if '_' in value:
        # price = value.split('_')[1].split(' ')[0].split(',')[0].split('.')[0]
        price = value.split('_')[1].split(' ')[0].split(',')[0].split('，')[0].split('.')[0]
        return float(price)
    return 0

def everfortune_determine_color(value):
    if 'ral1015' in value.lower():
        return 'Beige'
    elif 'ral5010' in value.lower():
        return 'Blue'
    else:
        return 'Unknown'

def everfortune_standardize_cities(value):
    if 'louis' in value.lower():
        return 'St. Louis'
    elif 'kansas' in value.lower():
        return 'Kansas City'
    elif 'tacoma' in value.lower():
        return 'Tacoma'
    elif 'seattle' in value.lower():
        return 'Tacoma'
    else:
        return value
    

#################################################
#                      Triton                   #
#################################################

def triton_determine_size_and_code(value):
    value = str(value).lower().replace(' ', '').strip()
    if value == '20':
        return '20 STD'
    elif value == '20hc':
        return '20 HC'
    elif value == '40':
        return '40 STD'
    elif value == '40hc':
        return '40 HC'
    else:
        return 'Unknown'

def triton_standardize_cities(value):
    if 'seattle' in value.lower():
        return 'Tacoma'
    else:
        return value

#################################################
#                    OVL                        #
#################################################

def ovl_standardize_cities(value):
    if 'st' in value.lower() and 'louis' in value.lower():
        return 'St. Louis'
    elif 'saint' in value.lower() and 'louis' in value.lower():
        return 'St. Louis'
    elif 'fort worth' in value.lower():
        return 'Dallas'
    elif 'los angeles' in value.lower():
        return 'Long Beach'
    elif 'seattle' in value.lower():
        return 'Tacoma'
    else:
        return value

def ovl_determine_color(value):
    if 'beige' in value.lower() and len(value.strip()) == 5:
        return 'Beige'
    else:
        return 'Unknown'

def ovl_determine_condition(value):
    if 'iicl' in value.lower():
        return 'PRM'
    elif 'damage' in value.lower():
        return 'DAMAGE'
    elif 'brand_new' in value.lower():
        return 'NEW'
    elif 'cargo_worthy' in value.lower():
        return 'CW'
    else:
        return 'Unknown'

def ovl_determine_size_and_code(value):
    if 'SD' in value.strip():
        return 'Remove'
    elif '20DC' in value.strip() and 'DD' in value.strip():
        return '20 STD DD'
    elif '20HC' in value.strip() and 'DD' in value.strip():
        return '20 HC DD'
    elif '20DC' in value.strip():
        return '20 STD'
    elif '20HC' in value.strip():
        return '20 HC'
    elif '40DC' in value.strip() and 'DD' in value.strip():
        return '40 STD DD'
    elif '40HC' in value.strip() and 'DD' in value.strip():
        return '40 HC DD'
    elif '40DC' in value.strip():
        return '40 STD'
    elif '40HC' in value.strip():
        return '40 HC'
    else:
        return 'Unknown'
    
#################################################
#                    Seaco                      #
#################################################

def seaco_standardize_cities(value):
    if isinstance(value, str):
        if 'los angeles' in value.lower():
            return 'Long Beach'
        if 'seattle' in value.lower():
            return 'Tacoma'
        else:
            return value
    else:
        return 'Unknown'

def seaco_determine_condition(value):
    if 'G-1' in value or 'G-2' in value:
        return 'CW'
    elif 'G-3' in value:
        return 'WWT'
    elif 'G-4' in value or 'G-5' in value:
        return 'DAMAGE'
    else:
        return 'Unknown'

def seaco_determine_size_and_code(value):
    if "20' Box Standard" in value:
        return '20 STD'
    elif "40' Box Standard" in value:
        return '40 STD'
    elif "40' High Cube Standard" in value:
        return '40 HC'
    else:
        return 'Unknown'
    
#################################################
#                    Florens                    #
#################################################

def florens_determine_size_and_code(value):
    value = str(value).lower().replace(' ', '').strip()
    if value == '20std':
        return '20 STD'
    elif value == '20hc':
        return '20 HC'
    elif value == '40std':
        return '40 STD'
    elif value == '40hc':
        return '40 HC'
    else:
        return 'Unknown'

def florens_standardize_cities(value):
    if 'seattle' in value.lower():
        return 'Tacoma'
    else:
        return value
    
#################################################
#                   Shipped                     #
#################################################

def shipped_determine_color(ralyom):
    # - only RAL1015 -> BEIGE
    # - only RAL5010 -> BLUE
    # - RAL1015 + RAL5010 -> BEIGE AND BLUE
    # - anything else -> UNKNOWN
    if isinstance(ralyom, str):
        ralyom_lower = ralyom.lower()
        if '1015' in ralyom_lower and '5010' in ralyom_lower:
            return 'Mixed'
        elif '1015' in ralyom_lower:
            return 'Beige'
        elif '5010' in ralyom_lower:
            return 'Blue'
        else:
            return 'Unknown'

def shipped_determine_condition(value):
    if 'NEW' in value:
        return 'NEW'
    elif 'CW' in value or 'WWT' in value:
        return 'WWT'
    elif 'IICL' in value:
        return 'PRM'
    elif 'DAMAGE' in value:
        return 'DAMAGE'
    else:
        return 'Unknown'
    
def shipped_determine_size_and_code(value):
    if "OS" in value.strip():
        return 'Unknown'
    elif "SD" in value.strip():
        return 'Unknown'
    elif "20DD" in value.strip():
        return '20 STD DD'
    elif "20HC" in value.strip():
        return '20 HC'
    elif "20" in value.strip():
        return '20 STD'
    elif "40HC" in value.strip():
        return '40 HC'
    elif "40HD" in value.strip():
        return '40 HC DD'
    elif "40SD" in value.strip():
        return '40 STD DD'
    elif "40" in value.strip():
        return '40 STD'
    else:
        return 'Unknown'

def shipped_standardize_cities(value):
    if 'seattle' in value.lower():
        return 'Tacoma'
    else:
        return value
    

#################################################
#                   BAL                         #
#################################################

def bal_standardize_cities(value):
    if isinstance(value, str):
        if 'seattle' in value.lower():
            return 'Tacoma'
        if 'st' in value.lower() and 'louis' in value.lower():
            return 'St. Louis'
        elif 'los angeles' in value.lower():
            return 'Long Beach'
        elif 'seattle' in value.lower():
            return 'Tacoma'
        else:
            return value
    else:
        return 'Unknown'
    
def bal_determine_size_and_code(value):
    if "20GP" in value.strip():
        return '20 STD'
    elif "40HQ" in value.strip():
        return '40 HC'
    elif "40GP" in value.strip():
        return '40 STD'
    else:
        return 'Unknown'
    
def bal_determine_condition(value):
    if 'new' in value.lower():
        return 'NEW'
    elif 'cw' in value.lower():
        return 'CW'
    elif 'DAMAGE' in value:
        return 'DAMAGE'
    else:
        return 'Unknown'

#################################################
#              CONTEIRA                         #
#################################################

# Function to send text to the Anthropic API
def send_to_llm_api_conteira(text):

    prompt = f"""Here is a page of shipping container inventory: <inventory>{text}</inventory>

    Extract it as a table with comma separated values that i can load into a pandas dataframe. 
    Please make sure you capture all the inventory that is in the page in the table.
    Go line by line so that you don't skip anything. Do not change any of the inventory or summarize any information.
    Do not add any extra text explaining what you did. Only output the CSV table.
    """
    return client.messages.create(
        model=MODEL_NAME,
        max_tokens=4096,
        messages=[{
            "role": 'user', "content":  prompt
        }]
    ).content[0].text

# Function to extract color information
def conteira_standardize_cities(value):
    if isinstance(value, str):
        if 'el' in value.lower() and 'paso' in value.lower():
            return 'El Paso'
        elif 'los angeles' in value.lower():
            return 'Long Beach'
        elif 'newark' in value.lower():
            return 'New York'
        elif 'seattle' in value.lower():
            return 'Tacoma'
        else:
            return value
    else:
        return 'Unknown'
    
def conteira_extract_color(note):
    # Ensure the input is a string (convert NaN or other types to empty string)
    if not isinstance(note, str):
        note = str(note)
    # Define patterns for RAL codes and color words (case insensitive)
    ral_1015_pattern = r'(RAL1015|1015|beige|Beige|BEIGE)'
    ral_5010_pattern = r'(RAL5010|5010|blue|Blue|BLUE)'
    
    # Check for BEIGE (RAL1015 or equivalent)
    has_1015 = bool(re.search(ral_1015_pattern, note, re.IGNORECASE))
    
    # Check for BLUE (RAL5010 or equivalent)
    has_5010 = bool(re.search(ral_5010_pattern, note, re.IGNORECASE))
    
    # Debugging prints
    #print(f"Note: {note} | has_1015: {has_1015}, has_5010: {has_5010}")
    
    # Apply the rules
    if has_1015 and has_5010:
        return "Mixed"
    elif has_1015:
        return "Beige"
    elif has_5010:
        return "Blue"
    else:
        return "Unknown"
    """note = str(note)
    match = re.search(r'/(RAL\d+)/', note)
    if match:
        return match.group(1)
    return None"""

"""def conteira_determine_color(ralyom):
    if isinstance(ralyom, str):
        ralyom_lower = ralyom.lower()
        if '1015' in ralyom_lower and '5010' in ralyom_lower:
            return 'Mixed'
        if 'ral1015' in ralyom_lower and 'ral5010' in ralyom_lower:
            return 'Mixed'
        elif '1015' in ralyom_lower or 'ral1015' in ralyom_lower:
            return 'Beige'
        elif '5010' in ralyom_lower or 'ral5010' in ralyom_lower:
            return 'Blue'
        else:
            return 'Unknown'"""
        
def conteira_determine_condition(value):
    if 'NEW' in value or '1st trip' in value or 'New' in value:
        return 'NEW'
    elif 'CW' in value or '3trips' in value or 'MULTI-TRIPS' in value:
        return 'CW'
    elif 'IICL5' in value or '2nd Trips' in value or '2nd Trip' in value or '2nd trips' in value:
        return 'PRM'
    elif 'DAMAGE' in value:
        return 'DAMAGE'
    else:
        return 'Unknown'

def conteira_determine_size_and_code(value):
    value = re.sub(r"[^\w\s]", "", value.strip()).lower()
    if "os" in value:
        return 'Unknown'
    if "duocon" in value:
        return 'Unknown'
    if "rh" in value:
        return 'Unknown'
    elif "20dd" in value:
        return '20 STD DD'
    elif "20hcdd" in value:
        return '20 HC DD'
    elif "20hc" in value:
        return '20 HC'
    elif "20dc" in value:
        return '20 STD'
    elif "20gp" in value:
        return '20 STD'
    
    elif "40hcdd" in value:
        return '40 HC DD'
    elif "40hc" in value:
        return '40 HC'
    elif "40dd" in value:
        return '40 STD DD'
    elif "40dc" in value:
        return '40 STD'
    elif "40dc" in value:
        return '40 STD'
    elif "40sd" in value:
        return '40 STD'
    elif "40gp" in value:
        return '40 STD'
    else:
        return 'Unknown'


#################################################
#              Logwin                           #
#################################################

def send_to_llm_api_logwin(text_content):

    user_prompt = """
    The attached text file contains an inventory list of shipping containers. the inventory is grouped by city (each city will have multiple containers listed below it as inventory). you must create a CSV table and place each inventory item in it. the table should have columns of: City and State, Location, Price, Type, Quantity, and Comment. The City and State, Location columns should repeat for each associated inventory entry (example below).
For example this raw data below: 
<raw_data>
l  Atlanta, GA

Location:  RoadOne (First Coast )

$2,100/20std new dark grey x 3 (LB & FLP & EOD)    

$3,300/40’HC new beige x 2 (LB & FLP & EOD)    

$4,000/40’HCDD new beige x 2 (LB & FLP & EOD)    

 

l  Charleston, SC

Location: Con Global

$3,200/40’HC new dark grey x 1 (LB & FLP & EOD)    

 

l  Charlotte, NC

N/A

 

l  Chicago, IL

Location: Con Global

$900/20std used x 2

$1,100/40std used x 2

$1,900/20std new beige x 9 (LB & FLP & EOD)    

$2,100/20std new dark grey x 1 (LB & FLP & EOD)    

$2,600/20’HC new beige x 3 (LB & FLP)

$3,200/40HC new beige x 5 (LB & FLP & EOD)    

$3,200/40HC new dark grey x 2 (LB & FLP & EOD)    

$3,600/40’HCDD new beige x 4 (LB & FLP & EOD)    

$6,400/40HCOS new beige x 1 ( 4 doors )
</raw_data>

should be mapped to the following output table structure 

<output>
City and State	Location	Price	Type	Quantity	Comment
Atlanta, GA	RoadOne (First Coast )	$2,100	20std new dark grey	3	(LB & FLP & EOD)
Atlanta, GA	RoadOne (First Coast )	$3,300	40’HC new beige	2	(LB & FLP & EOD)
Atlanta, GA	RoadOne (First Coast )	$4,000	40’HCDD new beige	2	(LB & FLP & EOD)
Charleston, SC	Con Global	$3,200	40’HC new dark grey	1	(LB & FLP & EOD)
Charlotte, NC					
Chicago, IL	Con Global	$900	20std used	2	
Chicago, IL	Con Global	$1,100	40std used	2	
Chicago, IL	Con Global	$1,900	20std new beige	9	(LB & FLP & EOD)
Chicago, IL	Con Global	$2,100	20std new dark grey	1	(LB & FLP & EOD)
Chicago, IL	Con Global	$2,600	20’HC new beige	3	(LB & FLP)
Chicago, IL	Con Global	$3,200	40HC new beige	5	(LB & FLP & EOD)
Chicago, IL	Con Global	$3,200	40HC new dark grey	2	(LB & FLP & EOD)
Chicago, IL	Con Global	$3,600	40’HCDD new beige	4	(LB & FLP & EOD)
Chicago, IL	Con Global	$6,400	40HCOS new beige	1	( 4 doors )
</output>

Extract all data in the attached text file and map it to a comma separated value (CSV) table format based on these instructions and examples. If a field is missing, just leave it blank (do not fill it with anything). If a numerical quantity for a row is not mentioned, make it 1. Do not summarize. Make sure to capture everything from the text file into the table.
ONLY RETURN THE CSV TABLE. DO NOT RETURN ANY TEXT OTHER THAN THE CSV TABLE.
    """

    message_list = [
        {
            "role": 'user',
            "content": [
                {"type": "text", "text": text_content},
                {"type": "text", "text": user_prompt}
            ]
        }
    ]

    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=4096,
        messages=message_list
    )
    # print(response.content[0].text)
    return response.content[0].text

def logwin_standardize_cities(value):
    if 'seattle' in value.lower():
        return 'Tacoma'
    else:
        return value

def logwin_determine_color(value):
    if 'beige' in value.lower():
        return 'Beige'
    else:
        return 'Unknown'

def logwin_determine_condition(value):
    if 'asis' in value.lower() or 'as-is' in value.lower() or 'as_is' in value.lower() or 'damage' in value.lower():
        return 'DAMAGE'
    elif 'new' in value.lower():
        return 'NEW'
    elif 'cw' in value.lower():
        return 'CW'
    else:
        return 'Unknown'    
def logwin_determine_size_and_code(value):
    value = re.sub(r"[^\w\s]", "", value.strip()).lower()
    if "os" in value:
        return 'Unknown'
    elif "duocon" in value:
        return 'Unknown'
    elif "rh" in value:
        return 'Unknown'
    
    elif "20dd" in value:
        return '20 STD DD'
    elif "20stddd" in value:
        return '20 STD DD'
    elif "20hcdd" in value:
        return '20 HC DD'
    elif "20hc" in value:
        return '20 HC'
    elif "20std" in value:
        return '20 STD'
    
    elif "40hcdd" in value:
        return '40 HC DD'
    elif "40hc" in value:
        return '40 HC'
    elif "40dd" in value:
        return '40 STD DD'
    elif "40stddd" in value:
        return '40 STD DD'
    elif "40std" in value:
        return '40 STD'
    
    else:
        return 'Unknown'
    
#################################################
#              OBLL                             #
#################################################

def send_to_llm_api_obll(text_content):

    user_prompt = """
    The attached text file contains an inventory list of shipping containers. the inventory is grouped by city (each city will have multiple containers listed below it as inventory). you must create a CSV table and place each inventory item in it. the table should have columns of: City, Quantity, Container, Condition, ColorCode, Location, Price, and ExtraComment. The City should repeat for each associated inventory entry (example below).
For example this raw data below: 
<raw_data>
Atlanta
4 x 20GPDD, New, RAL1015 FLP LBX, CGI, $2600

1 x 20GP, New, RAL1015 FLP LBX, CGI, $2450

 
1 x 40HC, New, RAL1015 FLP LBX, in ConGlobal, $3150, with a dent, pics available.

4 x 40HC, New, RAL1015 FLP LBX, in ConGlobal, $3550

4 x 40HC, IICL, YOM2018-2021 RAL5010, $2850, Roadone

6 x 40HCDD, New, RAL1015 FLP LBX, $3900, CGI

3 x 40HC, New, RAL3009, leasing spec, gatebuy $2800, ETA Sep 6/13

Baltimore
8 x 40HC, IICL, RAL5010/1015, $3100, CDI

30 x 40HC, 2-3 trips, RAL5010/5013/5003, $3200, CDI

1 x 40HCOS, 2 doors wide post, New, RAL7035 FLP LBX, $7200,CDI

Calgary
6 x 20DD, New, RAL1015 FLP LBX, $2550, Yellow Dog

6 x 20OS, New, RAL1015 FLP LBX, $5100, Yellow Dog

 
12 x 40HC, New, RAL1015 FLP LBX $3450, Yellow Dog

3 x 40HC, New, RAL1015 FLP LBX, gatebuy $3450, ETA Sep 25

1 x 40HC, New, RAL1015 FLP LBX EOD, gatebuy $3450, ETA Oct 14

Charleston
1 x 20GP, New, RAL1015 FLP LBX EOD, ConGlobal, $2000

1 x 20OS, New, RAL1015 FLP LBX, $4900, CGI

4 x 40HC, IICL, YOM2020-2022 blue, $2800, MRS-CMC

1 x 40HCOS, 4 doors, New, RAL1015 FLP LBX,$6800, MRS-CMC

14 x 40HC, New, RAL1015 FLP LBX, gatebuy $3350, ETA Oct 11-22. 7 EOD units.

2 x 40HCDD, New, RAL1015 FLP LBX, $3900, CGI.
</raw_data>

should be mapped to the following output table structure 

<output>
City    Quantity    Container   Condition   ColorCode   Location    Price   ExtraComment
Atlanta 4   20GPDD  New RAL1015 FLP LBX CGI $2600
Atlanta 1   20GP    New RAL1015 FLP LBX CGI $2450
Atlanta 1   40HC    New RAL1015 FLP LBX in ConGlobal    $31150  with a dent, pics available
Atlanta 4   40HC    New RAL1015 FLP LBX in ConGlobal    $3550
Atlanta 4   40HC    IICL    YOM2018-2021 RAL5010        $2850   Roadone
Atlanta 6   40HCDD  New RAL1015 FLP LBX     $3900   CGI
Atlanta 3   40HC    New RAL3009 leasing spec, gatebuy   $2800   ETA Sep 6/13
Baltimore   8   40HC    IICL    RAL5010/1015        $3100   CDI
Baltimore   30  40HC    2-3 trips   RAL5010/5013/5003       $3200   CDI
Baltimore   1   40HCOS  2 doors wide post   New RAL7035 FLP LBX     $7200   CDI
Calgary 6   20DD    New RAL1015 FLP LBX     $2550   Yellow Dog
Calgary 6   20OS    New RAL1015 FLP LBX     $5100   Yellow Dog
Calgary 12  40HC    New RAL1015 FLP LBX     $3450   Yellow Dog
Calgary 3   40HC    New RAL1015 FLP LBX gatebuy $3450   ETA Sep 25
Calgary 1   40HC    New RAL1015 FLP LBX EOD gatebuy $3450   ETA Oct 14
Charleston  1   20GP    New RAL1015 FLP LBX EOD ConGlobal   $2000
Charleston  1   20OS    New RAL1015 FLP LBX      $4900  CGI
Charleston  4   40HC    IICL    YOM2020-2022 blue       $2800   MRS-CMC
Charleston  1   40HCOS, 4 doors New RAL1015 FLP LBX      $6800 MRS-CMC
Charleston  14  40HC    New RAL1015 FLP LBX gatebuy $3350   ETA Oct 11-22. 7 EOD units.
Charleston  2   40HCDD  New RAL1015 FLP LBX     $3900   CGI.
</output>

Extract all data in the attached text file and map it to a comma separated value (CSV) table format based on these instructions and examples. If a field is missing, just leave it blank (do not fill it with anything). If a numerical quantity for a row is not mentioned, make it 1. Do not summarize. Make sure to capture everything from the text file into the table.
ONLY RETURN THE CSV TABLE. DO NOT RETURN ANY TEXT OTHER THAN THE CSV TABLE.
    """

    message_list = [
        {
            "role": 'user',
            "content": [
                {"type": "text", "text": text_content},
                {"type": "text", "text": user_prompt}
            ]
        }
    ]

    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=4096,
        messages=message_list
    )
    # print(response.content[0].text)
    return response.content[0].text

def obll_standardize_cities(value):
    if 'newark' in value.lower():
        return 'New York'
    elif 'seattle' in value.lower():
        return 'Tacoma'
    elif 'st.louis' in value.lower():
        return 'St. Louis'
    else:
        return value
    
def obll_determine_color(ralyom):
    # - only RAL1015 -> BEIGE
    # - only RAL5010 -> BLUE
    # - RAL1015 + RAL5010 -> BEIGE AND BLUE
    # - anything else -> UNKNOWN
    if isinstance(ralyom, str):
        ralyom_lower = ralyom.lower()
        if '1015' in ralyom_lower and '5010' in ralyom_lower:
            return 'Mixed'
        elif '1015' in ralyom_lower or 'blue' in ralyom_lower:
            return 'Beige'
        elif '5010' in ralyom_lower or 'beige' in ralyom_lower:
            return 'Blue'
        else:
            return 'Unknown'
        
def obll_determine_condition(value):
    if 'New' in value or '2 trips' in value:
        return 'NEW'
    elif 'CW' in value:
        return 'CW'
    elif 'IICL' in value or '2-3 trips' in value or '3' in value:
        return 'PRM'
    elif 'damaged' in value or 'AS IS' in value:
        return 'DAMAGE'
    else:
        return 'Unknown'
    
def obll_determine_size_and_code(value):
    value = re.sub(r"[^\w\s]", "", value.strip()).lower()
    if "os" in value:
        return 'Unknown'
    elif "rh" in value:
        return 'Unknown'
    elif "20gpdd" in value:
        return '20 STD DD'
    elif "40hcdd" in value:
        return '40 HC DD'
    elif "40hc" in value:
        return '40 HC'
    elif "20hcdd" in value:
        return '20 HC DD'
    elif "20gp" in value:
        return '20 STD'
    elif "20dd" in value:
        return '20 DD'    
    elif "20hc" in value:
        return '20 HC'
    elif "40gp" in value:
        return '40 STD'
    else:
        return 'Unknown'