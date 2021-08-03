"""
Created: 2021-05-03
Alex Hegeman | ahegem1@gmail.com

Classes for nutrition application
"""
import json
import datetime
from datetime import datetime
import pandas as pd
from urllib.request import urlopen, Request
from urllib.parse import quote, urlencode

# read in dri reference table
basepath = "/Users/Alex/Documents/lifestyle/food/nutrition/data/prod" 
fname1 = basepath + "/nutrient_ref_final.txt"
fname2 = basepath + "/unit_lkup.txt"
dri_ref = pd.read_csv(fname1, encoding='utf-8')
unit_lkup = pd.read_csv(fname2, encoding='utf-8')

class QueryResult:
    def __init__(self, query, source="SR Legacy", num_results=20):
        # define search parameters
        # for initial testing, user will need to input their
        # unique API key in the api_key parameter below:
        api_key = ''
        base_url = 'https://api.nal.usda.gov/fdc/v1'
        params = dict()
        params['query'] = query
        params['dataType'] = source
        params['pageSize'] = num_results
        params['api_key'] = api_key
        # create endpoint url and get search results for 'Avocado'
        url = base_url + "/foods/search?" + urlencode(params)
        with urlopen(url) as httpcon:
            results_str = httpcon.read().decode()
        results = json.loads(results_str)
        self.results = results
        
    def lookup(self):
        for i in range(len(self.results['foods'])):
            print(i, '-', self.results['foods'][i]['description'])
        
        idx = int(input('Enter id for desired food item:'))
        return(Food(self.results['foods'][idx]))

class User:
    # todo - for production will want to keep track od users
    # via unique ids and use these to pass to any other
    # classes than associate with a uniqu user
    def __init__(self, name):
        self.name = name
        self.join_date = datetime.now()
        self.daylist = []

    def __str__(self):
        return "Name: {}\nAge: {}\nWeight: {}".format(self.name, self.age, self.weight)

    def get_join_date(self):
        return self.join_date

    def set_age(self):
        self.age = int(input('Enter your age:'))

    def set_sex(self):
        sex_str = input("Enter sex: (M,F):")
        self.sex = 1 if sex_str.upper() == "M" else 2

    def set_weight(self):
        self.weight = int(input("Enter weight in lbs:"))
        
    def add_day(self, daydate = datetime.now().date()):
        newday = Day(daydate, self)
        self.daylist.append(newday)

    def show_daylist(self, num_days=7):
        daylist_copy = self.daylist.copy()
        daylist_copy.reverse()
        print('Last ', num_days, ' days:\n' + '-'*12)
        for d in daylist_copy[:num_days]:
            print(d)
        print('-'*12 + '\n' + str(len(self.daylist)), 'total days for', self.name)
    
    def get_daylist(self, num_days=7):
        daylist_copy = self.daylist.copy()
        daylist_copy.reverse()
        return daylist_copy[:num_days]
    
    def get_day(self, daydate):
        for d in self.daylist:
            if d.daydate == daydate:
                return d
        return None

class Day:
    def __init__(self, daydate, user):
        self.daydate = daydate
        self.user = user
        self.foodlist = []
        
    def __str__(self):
        # todo - could display more high-level summary info here maybe
        return "Date: {}\nUser: {}\n{} food items".format(self.daydate, self.user.name, len(self.foodlist))
    
    def add_food(self, food_object):
        # todo - validate unique food item before adding
        self.foodlist.append(food_object)
        food_object.day = self
        
    def show_foodlist(self):
        print("\n".join([f.details['description'] for f in self.foodlist]))
    
    def get_foodlist(self):
        return self.foodlist.copy()


class Food:
    # todo - need unique ids for food items, at least within a given day/foodlist
    # need to be able to manipule, delete, etc. by unique id.
    def __init__(self, details):
        self.details = details
        self.name = details['description']
        self.id_fdc = details['fdcId']
        self.id_ndb = details['ndbNumber']
        self.day = None
        self.weight_grams = None
        # self.user = None
        
    def __str__(self):
        return self.name
    
    def get_keys(self):
        return self.details.keys()
    
    def get_id_fdc(self):
        return self.id_fdc
    
    def get_id_ndb(self):
        return self.id_ndb
    
    def add_to_day(self, day_object):
        day_object.add_food(self)
        self.day = day_object
        # self.user = day_object.user
        return 1
    
    def show_portions(self):
        pass
        
    def find_nutrient(self, search_val, verbose=False):
        match_list = []
        match_idx = []
        for i in range(len(self.details['foodNutrients'])):
            n = self.details['foodNutrients'][i]
            if search_val.lower() in n['nutrientName'].lower():
                match_list.append("{} - {} {}".format(n['nutrientName'], n['value'], n['unitName']))
                match_idx.append(i)
        if verbose:
            if len(match_list) < 1:
                print("No matching nutrients found.")
            else:
                match_list.sort()
                print("\n".join(match_list))
        return match_idx
    
    def find_nonzero_nutrients(self, verbose=False):
        match_list = []
        match_idx = []
        for i in range(len(self.details['foodNutrients'])):
            n = self.details['foodNutrients'][i]
            if n['value'] > 0:
                match_list.append("{} - {} {}".format(n['nutrientName'], n['value'], n['unitName']))
                match_idx.append(i)
        if verbose:
            if len(match_list) < 1:
                print("No matching nutrients found.")
            else:
                match_list.sort()
                print("\n".join(match_list))
        return match_idx
    
    def get_nutrient(self, idx):
        details = self.details['foodNutrients'][idx]
        return Nutrient(details, self)
        
    def get_efa_ratio(self):
        #todo - need to account for correct logic here
        # sometimes we don't want to simply add all 18:3 or n-3 because
        # one may represent the total of the others
        n3_list = []
        n6_list = []
        for f in self.details['foodNutrients']:
            nutrient_name = f['nutrientName'].lower()
            if 'pufa' in nutrient_name:
                if '18:3' in nutrient_name or 'n-3' in nutrient_name:
                    print('{} - {}'.format(nutrient_name, f['value']))
                    n3_list.append(f['value'])
                elif '18:2' in nutrient_name or 'n-6' in nutrient_name:
                    print('{} - {}'.format(nutrient_name, f['value']))
                    n6_list.append(f['value'])
                else:
                    continue
        n3_total = sum(n3_list)
        n6_total = sum(n6_list)
        if (n3_total == 0) & (n6_total > 0):
            efa_ratio = 1
        elif n6_total == 0:
            efa_ratio = 0
        else:
            efa_ratio = round(n6_total / n3_total, 2)
        return efa_ratio

class Nutrient:
    def __init__(self, details, food_object):
        self.details = details
        self.food = food_object
        self.nutrient_number = int(details['nutrientNumber'])
        self.name = details['nutrientName']
        self.unit = details['unitName']
        self.value = details['value']
        
    def __str__(self):
        return "{}: {} {}".format(self.name, self.value, self.unit)
    
    def get_food(self):
        return self.foodId
    
    def get_value(self):
        return self.value
    
    def get_unit(self):
        return self.unit
    
    def get_dri(self, dri_ref=dri_ref):
        # todo - convert from reported 100g-equivalent nutrient values
        # so that we aren't showing a little dried thyme as having 1500%
        # our iron DV :) 
        matchrow = dri_ref[(dri_ref.nutrient_ndb_num == self.nutrient_number) \
                           & (dri_ref.sex == self.food.day.user.sex) \
                           & (self.food.day.user.age <= dri_ref.age_max) \
                           & (self.food.day.user.age >= dri_ref.age_min)]
        
        if matchrow.shape[0] < 1:
            print('No DRI for {}. File expansion request at fakeemail@gzz.com'.format(self.name))
            return None
        dri_val = matchrow.value[matchrow.index[0]]
        dri_unit = matchrow.unit_cd_nih[matchrow.index[0]]
        unit_lkup_match = unit_lkup[unit_lkup.code == dri_unit]
        dri_unit_str = unit_lkup_match.desc_short[unit_lkup_match.index[0]]
        
        if dri_unit_str == self.get_unit().lower():
            fdc_dri_pct = self.get_value() / dri_val
            print("{}: {}{} | DRI: {}{} | DV: {}%".format(self.food.get_id_ndb(),  \
                                         self.get_value(), self.get_unit(), \
                                         dri_val, dri_unit_str, round(fdc_dri_pct*100)))
        else:
            print('Non-matching units. Tell Alex to get off his ass and finish this method!')
